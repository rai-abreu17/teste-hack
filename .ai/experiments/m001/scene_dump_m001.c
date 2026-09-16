#define BOXFLOW_HOST
#include "../../../wokwi/boxflow-lidar.chip.c"

#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

static int oracle(Scene input) {
  Scene s = sanitize(input);
  Mesh m = scene_mesh(&s);
  float x, y, z;
  while (scanf("%f %f %f", &x, &y, &z) == 3) {
    Vec target = vec(x, y, z);
    Vec delta = sub(target, s.origin);
    float distance = sqrtf(dot(delta, delta));
    if (!(distance > 1e-6f)) {
      puts("1");
      continue;
    }
    Vec direction = mul(delta, 1.0f / distance);
    float nearest = INFINITY;
    for (int k = 0; k < m.count; k++) {
      nearest = fminf(nearest, intersect_triangle(s.origin, direction, m.triangles[k]));
    }
    if (s.obstacle) nearest = fminf(nearest, intersect_beam(s.origin, direction));
    puts(nearest >= distance - 1e-4f ? "1" : "0");
  }
  return ferror(stdin) ? 1 : 0;
}

// Native harness: frame mode preserves the old positional arguments and adds
// originX/originY at positions 11/12. Oracle mode is evaluator-only and reads
// target points (x y z) from stdin, one per line.
int main(int argc, char **argv) {
#ifdef _WIN32
  _setmode(_fileno(stdout), _O_BINARY);
#endif
  Scene s = default_scene();
  if (argc > 1 && strcmp(argv[1], "--oracle") == 0) {
    if (argc > 2) s.fill = strtof(argv[2], NULL);
    if (argc > 3) s.shape = atoi(argv[3]);
    if (argc > 4) s.center_x = strtof(argv[4], NULL);
    if (argc > 5) s.obstacle = atoi(argv[5]);
    if (argc > 6) s.origin.z = strtof(argv[6], NULL);
    if (argc > 7) s.origin.x = strtof(argv[7], NULL);
    if (argc > 8) s.origin.y = strtof(argv[8], NULL);
    return oracle(s);
  }

  uint32_t seq = 1;
  if (argc > 1) s.fill = strtof(argv[1], NULL);
  if (argc > 2) s.shape = atoi(argv[2]);
  if (argc > 3) s.center_x = strtof(argv[3], NULL);
  if (argc > 4) s.obstacle = atoi(argv[4]);
  if (argc > 5) s.dropout = strtof(argv[5], NULL);
  if (argc > 6) s.range = strtof(argv[6], NULL);
  if (argc > 7) seq = (uint32_t)strtoul(argv[7], NULL, 10);
  if (argc > 8) s.yaw = strtof(argv[8], NULL);
  if (argc > 9) s.tilt = strtof(argv[9], NULL);
  if (argc > 10) s.origin.z = strtof(argv[10], NULL);
  if (argc > 11) s.origin.x = strtof(argv[11], NULL);
  if (argc > 12) s.origin.y = strtof(argv[12], NULL);
  uint8_t data[BF_MAX_BYTES];
  size_t n = generate_frame(s, seq, (uint64_t)seq * 3000, data);
  return fwrite(data, 1, n, stdout) == n ? 0 : 1;
}
