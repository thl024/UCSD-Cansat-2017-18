/********************************************************************************************
 * glider.h
 * 
 * Initialize glider parameters to include in glider.ino
 * Initialize struct for packets
 *******************************************************************************************/

typedef struct packet{
  int state = 0;
  float pres = 0; 
  float temp = 0; 
  float alt = 0;
  float airspeed = 0; 
  float magx = 0;
  float magy = 0;
  float magz = 0;
  float accx = 0;
  float accy = 0;
  float accz = 0;
  float lat = 0;
  float lon = 0;
  float gpsalt = 0;
  int piccount = 0;
  int satnum = 0;
  float vel = 0;
  float netforce = 0;
  unsigned long missiontime = 0;
  float volt = 0;
  int packetcount = 0;
    
} data_s;

