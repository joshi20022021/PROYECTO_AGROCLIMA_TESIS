"""
Lector de Arduino para AgroClima GT.
Sensores físicos del proyecto:
    - DS18B20              → temperatura sonda (°C)     → campo: "t"
    - TSL2561              → intensidad de luz (lux)    → campo: "lux"
    - TCS3200              → color R,G,B (cuentas)      → campos: "cr","cg","cb"
                             El sistema calcula greenness_idx = cg/(cr+cg+cb)*100
    - Higrómetro capacitivo → humedad suelo (0.0-1.0)  → campo: "sm"

Formato JSON enviado por el Arduino (Serial, 9600 baud):
    {"t":22.5,"lux":32000,"cr":145,"cg":210,"cb":98,"sm":0.31}

Librerías Arduino necesarias (instalar desde Library Manager):
    - OneWire               (para DS18B20)
    - DallasTemperature     (para DS18B20)
    - Adafruit TSL2561      (para TSL2561)
    - Wire                  (incluida, para I2C del TSL2561)

Conexiones:
    DS18B20  DATA → D2  (con resistencia pull-up 4.7kΩ entre DATA y VCC)
    TSL2561  SDA  → A4, SCL → A5, VCC → 3.3V
    TCS3200  OUT  → D8, S0 → D4, S1 → D5, S2 → D6, S3 → D7, VCC → 5V
    Higrom.  AOUT → A0, VCC → 3.3V o 5V

Sketch Arduino (copiar en IDE):
------------------------------------------------------------
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include <Adafruit_TSL2561_U.h>

// DS18B20
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature ds18b20(&oneWire);

// TSL2561
Adafruit_TSL2561_Unified tsl(TSL2561_ADDR_FLOAT, 12345);

// TCS3200
#define S0 4
#define S1 5
#define S2 6
#define S3 7
#define OUT_PIN 8

// Higrómetro capacitivo
#define SOIL_PIN A0
#define SOIL_DRY  750   // calibrar: lectura en seco
#define SOIL_WET  280   // calibrar: lectura en agua

void setup() {
  Serial.begin(9600);
  ds18b20.begin();
  tsl.begin();
  tsl.enableAutoRange(true);
  tsl.setIntegrationTime(TSL2561_INTEGRATIONTIME_101MS);
  pinMode(S0, OUTPUT); pinMode(S1, OUTPUT);
  pinMode(S2, OUTPUT); pinMode(S3, OUTPUT);
  pinMode(OUT_PIN, INPUT);
  digitalWrite(S0, HIGH); digitalWrite(S1, LOW); // escala 20%
}

long readColor(int s2val, int s3val) {
  digitalWrite(S2, s2val); digitalWrite(S3, s3val);
  return pulseIn(OUT_PIN, LOW, 100000);
}

void loop() {
  // DS18B20
  ds18b20.requestTemperatures();
  float temp = ds18b20.getTempCByIndex(0);

  // TSL2561
  sensors_event_t event;
  tsl.getEvent(&event);
  float lux = event.light;

  // TCS3200 (R, G, B como frecuencias inversas — menor = más color)
  long cr = readColor(LOW,  LOW);
  long cg = readColor(HIGH, HIGH);
  long cb = readColor(LOW,  HIGH);

  // Higrómetro capacitivo (invertido: más bajo = más húmedo)
  int raw = analogRead(SOIL_PIN);
  float sm = 1.0 - constrain((raw - SOIL_WET) / (float)(SOIL_DRY - SOIL_WET), 0.0, 1.0);

  Serial.print("{\"t\":"); Serial.print(temp, 1);
  Serial.print(",\"lux\":"); Serial.print(lux, 0);
  Serial.print(",\"cr\":"); Serial.print(cr);
  Serial.print(",\"cg\":"); Serial.print(cg);
  Serial.print(",\"cb\":"); Serial.print(cb);
  Serial.print(",\"sm\":"); Serial.print(sm, 3);
  Serial.println("}");

  delay(2000);
}
------------------------------------------------------------
"""

import json
import threading
import time
from datetime import datetime
from typing import Callable, Optional

import serial
import serial.tools.list_ports

# Alias cortos que puede enviar el Arduino
_ALIASES = {
    # DS18B20
    "t":            "temperature",
    "temp":         "temperature",
    # TSL2561
    "lux":          "light_lux",
    "light":        "light_lux",
    # TCS3200 canales de color
    "cr":           "color_r",
    "cg":           "color_g",
    "cb":           "color_b",
    # Higrómetro capacitivo
    "sm":           "soil_moisture",
    "soil":         "soil_moisture",
    # Opcionales (si el usuario conecta sensores extra)
    "h":            "humidity",
    "hum":          "humidity",
    "r":            "rainfall",
    "rain":         "rainfall",
    "ph":           "soil_ph",
}

# Solo los 4 sensores físicos son obligatorios
_REQUIRED = {"temperature", "light_lux", "color_r", "color_g", "color_b", "soil_moisture"}


class ArduinoReader:
    """
    Lee datos del Arduino en un hilo de fondo y llama a `on_data`
    cada vez que llega una lectura válida.
    """

    def __init__(self, baud_rate: int = 9600, on_data: Callable = None):
        self.baud_rate   = baud_rate
        self.on_data     = on_data or (lambda x: None)
        self.port        = None
        self.serial_conn: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._running    = False
        self.connected   = False
        self.last_reading: Optional[dict] = None
        self.error_msg   = ""

    # ------------------------------------------------------------------
    # Detección de puerto
    # ------------------------------------------------------------------

    @staticmethod
    def find_port() -> Optional[str]:
        """Busca automáticamente el puerto del Arduino."""
        keywords = ["arduino", "ch340", "ch341", "usb serial", "usb-serial",
                    "ftdi", "cp210", "atmega"]
        for p in serial.tools.list_ports.comports():
            desc = (p.description or "").lower()
            manuf = (p.manufacturer or "").lower()
            if any(k in desc or k in manuf for k in keywords):
                return p.device
        # Si hay un solo puerto COM disponible, intentar con ese
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return ports[0] if len(ports) == 1 else None

    @staticmethod
    def list_ports() -> list[dict]:
        return [
            {"device": p.device, "description": p.description or ""}
            for p in serial.tools.list_ports.comports()
        ]

    # ------------------------------------------------------------------
    # Parseo de datos
    # ------------------------------------------------------------------

    @staticmethod
    def parse_line(line: str) -> Optional[dict]:
        """
        Parsea una línea del Arduino. Acepta JSON o CSV.
        CSV esperado: temperature,humidity,rainfall,soil_ph,soil_moisture
        """
        line = line.strip()
        if not line:
            return None

        # Intentar JSON
        if line.startswith("{"):
            try:
                raw = json.loads(line)
                parsed = {}
                for k, v in raw.items():
                    key = _ALIASES.get(k.lower(), k.lower())
                    parsed[key] = float(v)
                if _REQUIRED.issubset(parsed.keys()):
                    return parsed
            except (json.JSONDecodeError, ValueError):
                pass

        # Intentar CSV (5 valores en orden)
        parts = line.split(",")
        if len(parts) == 5:
            try:
                keys = ["temperature", "humidity", "rainfall", "soil_ph", "soil_moisture"]
                return {k: float(v) for k, v in zip(keys, parts)}
            except ValueError:
                pass

        return None

    # ------------------------------------------------------------------
    # Hilo de lectura
    # ------------------------------------------------------------------

    def start(self, port: Optional[str] = None) -> bool:
        """Inicia la lectura serial en un hilo de fondo. Retorna True si conectó."""
        self.port = port or self.find_port()
        if not self.port:
            self.error_msg = "No se encontró ningún Arduino conectado."
            return False

        try:
            self.serial_conn = serial.Serial(self.port, self.baud_rate, timeout=2)
            time.sleep(2)  # espera reset del Arduino
            self.connected = True
            self.error_msg = ""
        except serial.SerialException as e:
            self.error_msg = str(e)
            return False

        self._running = True
        self._thread  = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False

    def _read_loop(self):
        while self._running:
            try:
                raw = self.serial_conn.readline().decode("utf-8", errors="ignore")
                data = self.parse_line(raw)
                if data:
                    # Calcular índice de verdor desde TCS3200
                    cr = data.get("color_r", 1)
                    cg = data.get("color_g", 1)
                    cb = data.get("color_b", 1)
                    total = cr + cg + cb
                    data["greenness_idx"] = round((cg / total * 100) if total > 0 else 50.0, 1)
                    data["timestamp"] = datetime.now().isoformat()
                    self.last_reading = data
                    self.on_data(data)
            except serial.SerialException:
                self.connected = False
                self.error_msg = "Conexión perdida con el Arduino."
                break
            except Exception:
                pass


# Instancia global compartida con api.py
reader = ArduinoReader()
