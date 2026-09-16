#define BOXFLOW_HOST
#include "../wokwi/boxflow-lidar.chip.c"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
// Native harness, same ray caster as the Wokwi chip. Emits the raw wire frame.
int main(int argc,char **argv){
#ifdef _WIN32
  _setmode(_fileno(stdout), _O_BINARY);
#endif
  Scene s=default_scene();uint32_t seq=1;
  if(argc>1)s.fill=strtof(argv[1],NULL);
  if(argc>2)s.shape=atoi(argv[2]);
  if(argc>3)s.center_x=strtof(argv[3],NULL);
  if(argc>4)s.obstacle=atoi(argv[4]);
  if(argc>5)s.dropout=strtof(argv[5],NULL);
  if(argc>6)s.range=strtof(argv[6],NULL);
  if(argc>7)seq=(uint32_t)strtoul(argv[7],NULL,10);
  if(argc>8)s.yaw=strtof(argv[8],NULL);
  if(argc>9)s.tilt=strtof(argv[9],NULL);
  if(argc>10)s.origin.z=strtof(argv[10],NULL);
  uint8_t data[BF_MAX_BYTES];size_t n=generate_frame(s,seq,(uint64_t)seq*3000,data);
  return fwrite(data,1,n,stdout)==n?0:1;
}
