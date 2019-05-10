import nnsim.module
from nnsim.nnsimStatsCollector import nnsimStatsCollector


class Finish(Exception):
    pass

class Simulator(object):
    def __init__(self, tb_module, dump_stats, stats_dir):
        self.tb_module = tb_module
        self.dump_stats = dump_stats
        self.clk_ticks = 0

        self.tb_module.__setup__()
        if self.dump_stats:
            self.stats_collector = nnsimStatsCollector(self.tb_module, stats_dir)

    def reset(self):
        self.tb_module.__reset__()
        self.clk_ticks = 0

    def run(self, num_ticks, verbose=False):
        curr_ticks = 0
        try:
            while (num_ticks is None) or (curr_ticks < num_ticks):
                if self.dump_stats:
                    self.stats_collector.collect_class_specification_stats()
                    self.stats_collector.collect_architecture_specification_stats()
                if verbose:
                    print("---- Tick #%d -----" % self.clk_ticks)
                self.tb_module.__tick__()
                if verbose:
                    print("---- NTick #%d ----" % self.clk_ticks)
                self.tb_module.__ntick__()
                self.clk_ticks += 1
                curr_ticks += 1
        except Finish as msg:
            if self.dump_stats:
                self.stats_collector.collect_access_stats()
                self.stats_collector.collect_io_traces()
                
            print("\ncyc %d: %s" % (self.clk_ticks, msg))
        except KeyboardInterrupt:
            pass
        

            

def run_tb(tb_module, nticks=None, verbose=False, dump_stats=False, stats_dir = None):
    sim = Simulator(tb_module, dump_stats, stats_dir)
    sim.reset()
    sim.run(nticks, verbose)

