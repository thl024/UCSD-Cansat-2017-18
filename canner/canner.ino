#include <Adafruit_GPS.h>
//#include <Adafruit_SSD1306.h>

#include <Wire.h>
#include <LPS.h> 
#include <LSM6.h>
#include <LIS3MDL.h>
#include "cannerdata.h"
#include <SD.h>
#include <Servo.h>
#include <math.h>


//------------MACROS--------------
#define BUZZER_PIN 10
#define SERVO_PIN 9
#define SERVO_CLOSED 0
#define SERVO_OPEN 180
#define LAUNCH_ACCEL_THRESH 5 //in g's
#define DATA_BUFFER_LENGTH 10
#define RELEASE_THRESH 400
//--------------------------------
//-----------GLOBALS--------------

LPS PTS; 
LIS3MDL MAG;
LSM6 ACC;
data_s candata[DATA_BUFFER_LENGTH]; 
HardwareSerial gpsSerial = Serial1; //read and print from serial port 1 on the GPS
Adafruit_GPS GPS(&gpsSerial); //need to use the address for the GPS serial
HardwareSerial Xbee = Serial2; //calls class to send data to serial 2 for the xbee
const int chipSelect = 4;

int packet_count = 0;

Servo releaseServo;

boolean usingInterrupt = true;
void useInterrupt(boolean); 

int pos = 0;

//--------------------------------


void setup() {
  // put your setup code here, to run once:

Serial.begin(9600);
Wire.begin();

if(! PTS.init()){
  Serial.println("Pressure and temperature sensor failed to initialize");
}
if(! MAG.init()){
  Serial.println("Magnetometer sensor failed to initialize");
}
if(! ACC.init()){
  Serial.println("Accelerometer failed to initialize");
}
  Serial.print("Initializing SD card...");
  // make sure that the default chip select pin is set to
  // output, even if you don't use it:
  pinMode(10, OUTPUT);
  
  // see if the card is present and can be initialized:
  if (!SD.begin(chipSelect)) {
    Serial.println("Card failed, or not present");
    // don't do anything more:
    return;
  }
  Serial.println("card initialized.");
PTS.enableDefault();
MAG.enableDefault();
GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ); 

releaseServo.attach(SERVO_PIN);

}

void getData(int pos){
  candata[pos].pres = PTS.readPressureMillibars();
  candata[pos].temp = PTS.readTemperatureC();
  candata[pos].alt = PTS.pressureToAltitudeMeters(candata[pos].pres);
  MAG.read();
  candata[pos].magx = MAG.m.x;
  candata[pos].magy = MAG.m.y;
  candata[pos].magz = MAG.m.z;
  candata[pos].accx = ACC.a.x;
  candata[pos].accy = ACC.a.y;
  candata[pos].accz = ACC.a.z;
  candata[pos].gpsalt = GPS.altitude;
  candata[pos].lat = GPS.lat;
  candata[pos].lon = GPS.lon;
  candata[pos].satnum = (int)GPS.satellites;
//---------RTC----------------
//  static bool ran == false;
//  if(GPS.satellites>=5 && ran == false){
//    gpsTime = GPS.hour*60*60*1000+GPS.minute*60*1000+GPS.seconds*1000;
//    unsigned long timenow = millis();
//    ran == true;
//  }
//  else gpsTime = 0;
//  candata[pos].missiontime = gpsTime + millis()-timenow;
// ---------------------------  
//-----Velocity calc------------ 
  unsigned long sum1;
  long sum2;
  long num;
  long den;
  for(int i = 0; i<10;i++){
    sum1 = 0;
    sum2 = 0;
    sum1+=candata[i].missiontime;
    sum2+=candata[i].alt;
  }
  unsigned long avgtime = sum1/DATA_BUFFER_LENGTH;
  int avgdist = sum2/DATA_BUFFER_LENGTH;
  for (int i = 0; i<10; i++){
    num += (candata[i].missiontime - avgtime)*(candata[i].alt - avgdist);
    den += pow(candata[i].missiontime - avgtime,2);
  }
  candata[pos].vel = num/den;
//-----------------------------
//-------net force-------------
  candata[pos].netforce = sqrt(pow(candata[pos].accx,2)+pow(candata[pos].accy,2)+pow(candata[pos].accz,2))/9.8;
//-----------------------------  
}
void useInterrupt(boolean v) {
  if (v) {
    // Timer0 is already used for millis() - we'll just interrupt somewhere
    // in the middle and call the "Compare A" function above
    OCR0A = 0xAF;
    TIMSK0 |= _BV(OCIE0A);
    usingInterrupt = true;
  } else {
    // do not call the interrupt function COMPA anymore
    TIMSK0 &= ~_BV(OCIE0A);
    usingInterrupt = false;
  }
}

void loop() {
  freqLimiterGet(pos,.01,1);
  state(pos);
  freqLimiterSend(pos,1,1);
  pos++;
  if(pos == DATA_BUFFER_LENGTH){
    pos = 0;
  }
}


//create a function that sends data (the struct) into a serial port on the arduino
void sendData(int pos){
  Xbee.print(candata[pos].state);
  Xbee.print(",");
  Xbee.print(candata[pos].pres); //print uses ASCII format (Serial.Write uses values instead of ASCII)
  Xbee.print(",");
  Xbee.print(candata[pos].temp);
  Xbee.print(",");
  Xbee.print(candata[pos].alt);Xbee.print(",");
  Xbee.print(candata[pos].airspeed);Xbee.print(",");
  Xbee.print(candata[pos].magx);Xbee.print(",");
  Xbee.print(candata[pos].magy);Xbee.print(",");
  Xbee.print(candata[pos].magz);Xbee.print(",");
  Xbee.print(candata[pos].lat);Xbee.print(",");
  Xbee.print(candata[pos].lon);Xbee.print(",");
  Xbee.print(candata[pos].gpsalt);Xbee.print(",");
  Xbee.print(candata[pos].piccount);
  Xbee.println();
}

//create a function that logs the data (the struct)
void logdata(int pos){
  File dataFile = SD.open("canlog.txt", FILE_WRITE);

  // if the file is available, write to it:
  if (dataFile) {
    dataFile.print(candata[pos].alt); dataFile.print(",");
    dataFile.print(candata[pos].temp); dataFile.print(",");
    dataFile.print(candata[pos].state);dataFile.print(",");
    dataFile.print(candata[pos].pres); dataFile.print(",");
    dataFile.print(candata[pos].airspeed); dataFile.print(",");
    dataFile.print(candata[pos].magx); dataFile.print(",");
    dataFile.print(candata[pos].magy); dataFile.print(",");
    dataFile.print(candata[pos].magz); dataFile.print(",");
    dataFile.print(candata[pos].lat); dataFile.print(",");
    dataFile.print(candata[pos].lon); dataFile.print(",");
    dataFile.print(candata[pos].gpsalt); dataFile.print(",");
    dataFile.print(candata[pos].piccount); dataFile.println();
    dataFile.close();
  }  
  // if the file isn't open, pop up an error:
  else {
    Serial.println("error opening datalog.txt");
  } 
}

void buzzerOn(){
  static bool ran = false;
  if(ran == false){
    digitalWrite(BUZZER_PIN,HIGH);
    ran = true;
  }
}

void buzzerOff(){
  digitalWrite(BUZZER_PIN,LOW);
}

int servoControl(bool servostate){
  if(servostate == false){
    releaseServo.write(SERVO_CLOSED);
  }
  else{
    releaseServo.write(SERVO_OPEN);
  }
  return releaseServo.read();
}

void state(int pos){
  if(candata[pos].state == 0 && candata[pos].netforce >= LAUNCH_ACCEL_THRESH){
     candata[pos].state = 1; 
  }
  else if(candata[pos].state == 1){
    if(candata[pos].alt<RELEASE_THRESH-10 && candata[pos].vel<=0){
      candata[pos].state=3;
    }
    else if(candata[pos].alt>RELEASE_THRESH-10){
      candata[pos].state = 2;
    }
  }
  else if(candata[pos].state == 2 && candata[pos].vel<=0 && candata[pos].alt <= RELEASE_THRESH + 10){
    candata[pos].state = 3;
  }
  else if(candata[pos].state = 3){
    servoControl(true);
    buzzerOn();
  } 
}

void freqLimiterGet(int pos, int per, int tol){
  static unsigned long last_send = 0;
  int this_send = millis();
  if (this_send - last_send > .5*per)  {
    if (this_send%1000 < tol*per/100. || this_send%1000 > (100-tol)*per/100)  {
      last_send = this_send;
      getData(pos);
    }
  }
}

void freqLimiterSend(int pos, int per, int tol){
  static unsigned long last_send = 0;
  unsigned long this_send = millis();
  if (this_send - last_send > .5*per)  {
    if (this_send%1000 < tol*per/100. || this_send%1000 > (100-tol)*per/100)  {
      last_send = this_send;
      //packet_count++;
      sendData(pos);
    }
  }
}






