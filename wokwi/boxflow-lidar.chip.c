// BoxFlow ToF Mock — VL53L5CX-inspired 8x8 ideal zone-center model.
// NOT a VL53L5CX register/firmware emulator or a physical measurement model.
// All scene dimensions below are hypothetical, in metres. See docs/GEOMETRIA.md.
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#ifndef BOXFLOW_HOST
#include "wokwi-api.h"
#endif

#define BF_MAX_COLS 8
#define BF_MAX_ROWS 8
#define BF_HEADER 64
#define BF_RECORD 10
#define BF_MAX_BYTES (BF_HEADER + BF_MAX_COLS * BF_MAX_ROWS * BF_RECORD)
#define BF_PI 3.14159265358979323846f

typedef struct { float x,y,z; } Vec;
typedef struct { Vec a,b,c; } Tri;
typedef struct {
  float fill, center_x, range, fov_x, fov_y, yaw, tilt, dropout;
  int shape, obstacle, cols, rows;
  Vec origin;
} Scene;
typedef struct { Tri triangles[64]; int count; } Mesh;

static float bound(float v,float lo,float hi) { return fminf(hi,fmaxf(lo,v)); }
static Vec vec(float x,float y,float z) { return (Vec){x,y,z}; }
static Vec sub(Vec a,Vec b) { return vec(a.x-b.x,a.y-b.y,a.z-b.z); }
static Vec mul(Vec a,float t) { return vec(a.x*t,a.y*t,a.z*t); }
static float dot(Vec a,Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
static Vec cross(Vec a,Vec b) { return vec(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x); }
static Vec unit(Vec a) { return mul(a,1.0f/sqrtf(dot(a,a))); }
static Vec rotate(Vec a,float yaw,float tilt) {
  float y=yaw*BF_PI/180, t=tilt*BF_PI/180;
  Vec b=vec(cosf(t)*a.x+sinf(t)*a.z,a.y,-sinf(t)*a.x+cosf(t)*a.z);
  return vec(cosf(y)*b.x-sinf(y)*b.y,sinf(y)*b.x+cosf(y)*b.y,b.z);
}
static void triangle(Mesh *m,Vec a,Vec b,Vec c) {
  if(m->count<64) m->triangles[m->count++]=(Tri){a,b,c};
}
static void quad(Mesh *m,Vec a,Vec b,Vec c,Vec d) { triangle(m,a,b,c);triangle(m,a,c,d); }
static void pyramid(Mesh *m,float cx,float cy,float w,float d,float h) {
  Vec a=vec(cx-w/2,cy-d/2,0),b=vec(cx+w/2,cy-d/2,0);
  Vec c=vec(cx+w/2,cy+d/2,0),e=vec(cx-w/2,cy+d/2,0),p=vec(cx,cy,h);
  triangle(m,a,b,p);triangle(m,b,c,p);triangle(m,c,e,p);triangle(m,e,a,p);
}
static Scene default_scene(void) {
  return (Scene){.fill=75,.center_x=.15f,.range=4,.fov_x=45,.fov_y=45,
    .yaw=0,.tilt=0,.dropout=0,.shape=0,.obstacle=0,.cols=8,.rows=8,
    .origin={.15f,.15f,.40f}};
}
static Scene sanitize(Scene s) {
  s.fill=bound(s.fill,0,100);s.center_x=bound(s.center_x,.10f,.20f);
  s.range=bound(s.range,.2f,4);s.fov_x=45;s.fov_y=45;
  s.yaw=bound(s.yaw,-20,20);s.tilt=bound(s.tilt,-15,15);s.dropout=bound(s.dropout,0,100);
  s.cols=8;s.rows=8;s.shape=(int)bound((float)s.shape,0,4);s.obstacle=!!s.obstacle;
  s.origin.x=bound(s.origin.x,.05f,.25f);s.origin.y=bound(s.origin.y,.05f,.25f);s.origin.z=bound(s.origin.z,.2f,.6f);
  return s;
}
static Mesh scene_mesh(const Scene *s) {
  Mesh m={0};
  // Hypothetical bench: 0.30 x 0.30 m, bases 0.01 m, walls 0.15 m.
  quad(&m,vec(0,0,.01f),vec(.01f,0,0),vec(.01f,.3f,0),vec(0,.3f,.01f));
  quad(&m,vec(.01f,0,0),vec(.29f,0,0),vec(.29f,.3f,0),vec(.01f,.3f,0));
  quad(&m,vec(.29f,0,0),vec(.3f,0,.01f),vec(.3f,.3f,.01f),vec(.29f,.3f,0));
  quad(&m,vec(0,0,0),vec(0,.3f,0),vec(0,.3f,.15f),vec(0,0,.15f));
  quad(&m,vec(.3f,0,0),vec(.3f,.3f,0),vec(.3f,.3f,.15f),vec(.3f,0,.15f));
  quad(&m,vec(0,.3f,0),vec(.3f,.3f,0),vec(.3f,.3f,.15f),vec(0,.3f,.15f));
  float h=.1f*s->fill/100;
  if(h<=0) return m;
  float x=s->center_x;
  if(s->shape==0) pyramid(&m,x,.15f,.15f,.15f,h);
  if(s->shape==1) { pyramid(&m,.09f,.15f,.10f,.10f,h);pyramid(&m,.21f,.15f,.10f,.10f,.7f*h); }
  if(s->shape==2) {
    Vec a=vec(x-.075f,.075f,h),b=vec(x+.075f,.075f,h),c=vec(x+.075f,.225f,h),d=vec(x-.075f,.225f,h);
    quad(&m,a,b,c,d);
    quad(&m,vec(a.x,a.y,0),vec(b.x,b.y,0),b,a);
    quad(&m,vec(b.x,b.y,0),vec(c.x,c.y,0),c,b);
    quad(&m,vec(c.x,c.y,0),vec(d.x,d.y,0),d,c);
    quad(&m,vec(d.x,d.y,0),vec(a.x,a.y,0),a,d);
  }
  if(s->shape==3) {
    Vec a=vec(x-.075f,.075f,0),b=vec(x+.075f,.075f,h),c=vec(x+.075f,.225f,h),d=vec(x-.075f,.225f,0);
    quad(&m,a,b,c,d);triangle(&m,a,vec(b.x,b.y,0),b);
    triangle(&m,d,c,vec(c.x,c.y,0));quad(&m,vec(b.x,b.y,0),vec(c.x,c.y,0),c,b);
  }
  if(s->shape==4) {
    // Constant material thickness above the known base: analytical V = 0.09*h.
    quad(&m,vec(0,0,.01f+h),vec(.01f,0,h),vec(.01f,.3f,h),vec(0,.3f,.01f+h));
    quad(&m,vec(.01f,0,h),vec(.29f,0,h),vec(.29f,.3f,h),vec(.01f,.3f,h));
    quad(&m,vec(.29f,0,h),vec(.3f,0,.01f+h),vec(.3f,.3f,.01f+h),vec(.29f,.3f,h));
  }
  return m;
}
static float intersect_triangle(Vec o,Vec d,Tri t) {
  Vec e1=sub(t.b,t.a),e2=sub(t.c,t.a),p=cross(d,e2);
  float det=dot(e1,p);if(fabsf(det)<1e-8f)return INFINITY;
  float inv=1/det;Vec s=sub(o,t.a);float u=dot(s,p)*inv;
  if(u < -1e-6f || u>1.000001f)return INFINITY;
  Vec q=cross(s,e1);float v=dot(d,q)*inv;
  if(v < -1e-6f || u+v>1.000001f)return INFINITY;
  float hit=dot(e2,q)*inv;return hit>1e-5f?hit:INFINITY;
}
static float intersect_beam(Vec o,Vec d) {
  float p[3]={o.x,o.y,o.z},v[3]={d.x,d.y,d.z};
  float lo[3]={.17f,0,.18f},hi[3]={.20f,.3f,.20f};
  float tmin=0,tmax=INFINITY;
  for(int i=0;i<3;i++) {
    if(fabsf(v[i])<1e-8f){if(p[i]<lo[i]||p[i]>hi[i])return INFINITY;continue;}
    float a=(lo[i]-p[i])/v[i],b=(hi[i]-p[i])/v[i];
    tmin=fmaxf(tmin,fminf(a,b));tmax=fminf(tmax,fmaxf(a,b));
    if(tmin>tmax)return INFINITY;
  }
  return tmin>1e-5f?tmin:INFINITY;
}
static void put16(uint8_t *b,uint16_t v) { b[0]=v&255;b[1]=v>>8; }
static void put32(uint8_t *b,uint32_t v) { for(int i=0;i<4;i++)b[i]=(v>>(8*i))&255; }
static void put64(uint8_t *b,uint64_t v) { for(int i=0;i<8;i++)b[i]=(v>>(8*i))&255; }
static void putfloat(uint8_t *b,float v) { uint32_t n;memcpy(&n,&v,4);put32(b,n); }
static uint32_t crc_step(uint32_t c,const uint8_t *b,size_t n) {
  while(n--){c^=*b++;for(int j=0;j<8;j++)c=(c>>1)^(0xedb88320u&-(int32_t)(c&1));}
  return c;
}
static uint32_t hash32(uint32_t a) { a^=a>>16;a*=0x7feb352du;a^=a>>15;a*=0x846ca68bu;return a^(a>>16); }
static size_t generate_frame(Scene input,uint32_t seq,uint64_t start_ms,uint8_t *frame) {
  Scene s=sanitize(input);Mesh m=scene_mesh(&s);
  size_t count=(size_t)s.cols*s.rows,len=BF_HEADER+count*BF_RECORD;
  memset(frame,0,len);memcpy(frame,"BFLD",4);frame[4]=2;frame[5]=1;
  put16(frame+6,BF_HEADER);put32(frame+8,seq);put64(frame+12,start_ms);put32(frame+20,100);
  put16(frame+24,s.cols);put16(frame+26,s.rows);put16(frame+28,BF_RECORD);put16(frame+30,3);
  putfloat(frame+32,s.origin.x);putfloat(frame+36,s.origin.y);putfloat(frame+40,s.origin.z);
  putfloat(frame+44,s.yaw);putfloat(frame+48,s.tilt);putfloat(frame+52,0);
  put16(frame+56,(uint16_t)lroundf(s.range*1000));put16(frame+58,(uint16_t)(count*BF_RECORD));
  for(int row=0;row<s.rows;row++)for(int col=0;col<s.cols;col++) {
    int i=row*s.cols+col;
    // IDEAL pinhole zone centers, nominal 45 degrees on each axis (ST Table 2).
    // Finite zone response, histograms and optical distortion are not simulated.
    float half=tanf(22.5f*BF_PI/180);
    float sx=(2*((float)col+.5f)/8-1)*half,sy=(2*((float)row+.5f)/8-1)*half;
    Vec u=unit(vec(sx,sy,-1)),d=rotate(u,s.yaw,s.tilt);
    float t=INFINITY;
    for(int k=0;k<m.count;k++)t=fminf(t,intersect_triangle(s.origin,d,m.triangles[k]));
    if(s.obstacle)t=fminf(t,intersect_beam(s.origin,d));
    uint8_t status=isfinite(t)?(t<=s.range?1:2):0;
    if(hash32((uint32_t)i^(seq*2654435761u))%10000 < (uint32_t)(s.dropout*100))status=0;
    uint8_t *r=frame+BF_HEADER+i*BF_RECORD;
    put16(r,status==1?(uint16_t)lroundf(t*1000):0);
    put16(r+2,(uint16_t)(int16_t)lroundf(u.x*32767));
    put16(r+4,(uint16_t)(int16_t)lroundf(u.y*32767));
    put16(r+6,(uint16_t)(int16_t)lroundf(u.z*32767));r[8]=status;
  }
  uint32_t c=crc_step(0xffffffffu,frame,60);
  c=crc_step(c,frame+BF_HEADER,len-BF_HEADER);put32(frame+60,c^0xffffffffu);
  return len;
}

#ifndef BOXFLOW_HOST
static uint16_t get16(const uint8_t *b) { return b[0]|((uint16_t)b[1]<<8); }
typedef struct {
  uint8_t frame[BF_MAX_BYTES]; size_t len; uint32_t seq;
  uint32_t attrs[16]; uint32_t freeze_attr,fault_attr;
  uint32_t width,height; buffer_t display; timer_t timer;
  uint16_t ptr; uint8_t address_bytes; bool busy; Scene pending; uint64_t started_ms;
} Chip;
// A tiny original 5x7 alphabet for the depth legend; no external font dependency.
static const uint8_t font[][5]={
  {126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},
  {127,73,73,73,65},{127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},
  {0,65,127,65,0},{32,64,65,63,1},{127,8,20,34,65},{127,64,64,64,64},
  {127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},{127,9,9,9,6},
  {62,65,81,33,94},{127,9,25,41,70},{38,73,73,73,50},{1,1,127,1,1},
  {63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},
  {7,8,112,8,7},{97,81,73,69,67}
};
static void label(Chip *c,int x,int y,const char *s) {
  for(;*s;s++,x+=6) if(*s>='A'&&*s<='Z')for(int i=0;i<5;i++)for(int j=0;j<7;j++) {
    uint8_t color[4]={220,232,240,255};
    if((font[*s-'A'][i]>>j)&1 && x+i>=0 && x+i<(int)c->width && y+j<(int)c->height)
      buffer_write(c->display,((y+j)*c->width+x+i)*4,color,4);
  }
}
static void draw(Chip *c) {
  uint8_t line[256*4];int cols=get16(c->frame+24),rows=get16(c->frame+26);
  const float color_scale_m=1.0f;
  for(uint32_t y=0;y<c->height;y++) {
    for(uint32_t x=0;x<c->width;x++) {
      uint8_t *p=line+x*4;p[0]=14;p[1]=25;p[2]=39;p[3]=255;
      if(y>=22&&y<170&&x>=8&&x<248) {
        int col=(x-8)*cols/240,row=(y-22)*rows/148;
        const uint8_t *r=c->frame+BF_HEADER+(row*cols+col)*BF_RECORD;
        if(r[8]==1){float t=bound((get16(r)/1000.0f)/color_scale_m,0,1);p[0]=(uint8_t)(240*(1-t));p[1]=(uint8_t)(90+120*t);p[2]=(uint8_t)(40+210*t);}
        else if(r[8]==2){p[0]=195;p[1]=75;p[2]=165;}else {p[0]=39;p[1]=48;p[2]=61;}
        if((x-8)*cols%240<cols || (y-22)*rows%148<rows){p[0]/=2;p[1]/=2;p[2]/=2;}
      }
      if(y>=183&&y<=188&&x>=8&&x<248){float t=(x-8)/240.0f;p[0]=(uint8_t)(240*(1-t));p[1]=(uint8_t)(90+120*t);p[2]=(uint8_t)(40+210*t);}
    }
    buffer_write(c->display,y*c->width*4,line,c->width*4);
  }
  label(c,8,7,"BOXFLOW TOF MOCK SIMULADO");label(c,8,173,"ZERO");label(c,140,173,"UM METRO OU MAIS");
  label(c,8,194,"CINZA SEM RETORNO");label(c,8,205,"ROSA FORA DO ALCANCE");
}
static Scene read_scene(Chip *c) {
  Scene s=default_scene();
  s.fill=attr_read_float(c->attrs[0]);s.shape=(int)attr_read_float(c->attrs[1]);
  s.center_x=attr_read_float(c->attrs[2]);s.obstacle=(int)attr_read_float(c->attrs[3]);
  s.dropout=attr_read_float(c->attrs[4]);s.range=attr_read_float(c->attrs[5]);
  s.yaw=attr_read_float(c->attrs[6]);s.tilt=attr_read_float(c->attrs[7]);
  s.origin=vec(attr_read_float(c->attrs[8]),attr_read_float(c->attrs[9]),attr_read_float(c->attrs[10]));
  return sanitize(s);
}
static void captured(void *data) {
  Chip *c=data;c->len=generate_frame(c->pending,++c->seq,c->started_ms,c->frame);c->busy=false;draw(c);
}
static bool connect_i2c(void *data,uint32_t address,bool reading) {
  Chip *c=data;(void)address;if(attr_read_float(c->fault_attr)>=.5f)return false;
  if(!reading){c->address_bytes=0;c->ptr=0;}return true;
}
static uint8_t read_i2c(void *data) {
  Chip *c=data;uint32_t p=c->ptr;if(c->ptr<65535)c->ptr++;
  if(p==5&&c->busy)return 0;
  return p<c->len?c->frame[p]:0xff;
}
static bool write_i2c(void *data,uint8_t v) {
  Chip *c=data;
  if(c->address_bytes<2){c->ptr=(c->ptr<<8)|v;c->address_bytes++;return true;}
  if(c->ptr!=0xffff || v!=0xa1 || c->busy)return false;
  if(attr_read_float(c->freeze_attr)>=.5f)return true;
  c->pending=read_scene(c);c->started_ms=get_sim_nanos()/1000000;c->busy=true;
  timer_start(c->timer,100000,false);return true;
}
void chip_init(void) {
  Chip *c=calloc(1,sizeof(Chip));if(!c)return;
  const char *names[]={"fill","shape","centerX","obstacle","dropout","rangeM","yaw","tilt","sensorX","sensorY","sensorZ"};
  const float values[]={75,0,.15f,0,0,4,0,0,.15f,.15f,.40f};
  for(int i=0;i<11;i++)c->attrs[i]=attr_init_float(names[i],values[i]);
  c->freeze_attr=attr_init_float("freeze",0);c->fault_attr=attr_init_float("i2cFault",0);
  pin_init("VCC",INPUT);pin_init("GND",INPUT);
  const i2c_config_t i2c={.address=0x42,.scl=pin_init("SCL",INPUT_PULLUP),.sda=pin_init("SDA",INPUT_PULLUP),
    .connect=connect_i2c,.read=read_i2c,.write=write_i2c,.user_data=c};
  i2c_init(&i2c);const timer_config_t t={.callback=captured,.user_data=c};c->timer=timer_init(&t);
  c->display=framebuffer_init(&c->width,&c->height);
  if(c->width!=256||c->height!=218){printf("BoxFlow: display must be 256x218\n");return;}
  c->len=generate_frame(read_scene(c),0,0,c->frame);draw(c);
  printf("BoxFlow ToF Mock: ideal VL53L5CX 8x8 profile, I2C 0x42, bench-vl53-30cm-v3, simulated\n");
}
#endif
