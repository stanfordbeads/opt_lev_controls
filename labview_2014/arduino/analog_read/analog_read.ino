#include <stdio.h>
#include <string.h>

int sensor_pin = A0;
int voltage;
int my_timeout = 250;

unsigned int read_time = 100;

unsigned int n, start, now;

float sum, avg, out_val;

String string_in = "";

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(my_timeout);
}



void read_data(int n_millisec) {
  n = 0;
  start = millis();
  sum = 0.;
  do
  {
     sum += analogRead(sensor_pin);
     n++;
     now = millis();
  }
  while (now < start + n_millisec);
  avg = sum / n;
  Serial.println(avg);
}






void loop() {
  char recipe = 0;
  
  if (Serial.available())
  {
    recipe = Serial.read();
  }
  
  switch (recipe)
  {
    case 'r':
      read_data(read_time);
      break;
  }
  
  recipe = 0;
  
}
