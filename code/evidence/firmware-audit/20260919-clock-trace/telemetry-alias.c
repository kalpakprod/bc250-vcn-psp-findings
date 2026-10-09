#include <assert.h>
#include <stdio.h>
struct M { int MemclkFrequency; };
struct G { int current_uclk,current_fclk,average_uclk_frequency,average_fclk_frequency; };
int main(void) { struct { struct M Current,Average; } metrics={{1750},{1333}}; struct G g={0},*gpu_metrics=&g;
gpu_metrics->average_uclk_frequency = metrics.Average.MemclkFrequency;
gpu_metrics->average_fclk_frequency = metrics.Average.MemclkFrequency;
gpu_metrics->current_uclk = metrics.Current.MemclkFrequency;
gpu_metrics->current_fclk = metrics.Current.MemclkFrequency;
assert(g.current_uclk==1750 && g.current_fclk==1750); assert(g.average_uclk_frequency==1333 && g.average_fclk_frequency==1333); puts("PASS: copied source assignments alias UCLK/FCLK for distinct Current/Average inputs"); return 0; }
