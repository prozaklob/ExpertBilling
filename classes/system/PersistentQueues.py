from __future__ import with_statement

import collections
from threading import Lock
import random, marshal, time
import os
import traceback

class FileSaveDeque(collections.deque):
    
    def __init__(self):
        super(collections.deque, self).__init__()
        self.prev_ps  = 1.0
        self.cur_ps   = 1.0
        self.allow_recover = 0
        self.allow_dump    = 0
        self.file_queue = collections.deque()
        self.file_lock = Lock()
        
    def post_init(self, name, dump_dir, prefix, file_pack, max_sendbuf_len, sui_lock, logger):
        self.name = name
        self.hpath  = ''.join((dump_dir,'/', prefix))        
        self.max_len = float(max_sendbuf_len)
        self.FILE_PACK = file_pack
        self.file_ps  = file_pack / self.max_len        
        self.LOCK = sui_lock        
        self.logger = logger
        self.file_lock = Lock()
    '''    
    def __init__(self, name, dump_dir, prefix, file_pack, max_sendbuf_len, sui_lock, logger):
        super(collections.deque, self).__init__()
        self.prev_ps  = 1.0
        self.cur_ps   = 1.0
        self.allow_recover = 0
        self.allow_dump    = 0
        self.file_queue = collections.deque()
        self.file_lock = Lock()
        
        self.name = name
        self.hpath  = ''.join((dump_dir,'/', prefix))        
        self.max_len = float(max_sendbuf_len)
        self.FILE_PACK = file_pack
        self.file_ps  = file_pack / self.max_len        
        self.LOCK = sui_lock        
        self.logger = logger'''

    def end_slice(self, count):
        rubbish = []
        self_len = len(self)
        if count >= self_len:
            rubbish = list(self)
        else:
            for i in xrange(count):
                val = self.pop()
                rubbish.append(val)
            rubbish.reverse()
        return rubbish
            
    def sui_check(self):
        fname, dfile = None, None

        try:
            #get a file name from a queue
            fname = None
            self.allow_recover = 0
            self.allow_dump    = 0
            #with queues.dbLock:
            self_len = len(self)
            self.cur_ps = self_len / self.max_len
            self.logger.info('%s: FileSaveDeque previous dbqueue len/max percentage: %s', (self.name, self.prev_ps))
            self.logger.info('%s: FileSaveDeque current dbqueue len/max percentage: %s', (self.name, self.cur_ps))
            if self.cur_ps > 1:
                if self.cur_ps < 1 + self.file_ps:
                    pass
                elif self.prev_ps < 1 and (self.cur_ps - 1) / self.file_ps < 3:
                    self.allow_dump = 1
                else:
                    self.allow_dump = int((self.cur_ps - 1) / self.file_ps)
            elif self.cur_ps < 1 and len(self.file_queue) > 0:
                if self.cur_ps > 1 - self.file_ps:
                    pass
                elif self.prev_ps > 1 and  (1 - self.cur_ps) / self.file_ps < 3:
                    self.allow_recover = 1
                else:
                    self.allow_recover = int((1 - self.cur_ps) / self.file_ps)
                    
            self.prev_ps = self.cur_ps
            if self.allow_dump:
                dump_queue = None
                dump_index = self.allow_dump * self.FILE_PACK
                with self.LOCK:
                    dump_queue = self.end_slice(dump_index)
                    #dump_queue = self[dump_index:]
                    #del self[dump_index:]
                if dump_queue:
                    for i in xrange(self.allow_dump):
                        dump_out = dump_queue[:self.FILE_PACK]
                        dump_queue = dump_queue[self.FILE_PACK:]
                        if dump_out:
                            try:
                                fname = ''.join((self.hpath, str(time.time()), '_', str(random.random()), '.dmp'))
                                dump_file = open(fname, 'wb')
                                marshal.dump(dump_out, dump_file)
                                dump_file.close()
                            except Exception, ex:
                                self.logger.error("%s: FileSaveDeque filewrite exception: %s \n %s", (self.name, repr(ex), traceback.format_exc()))
                            else:
                                with self.file_lock:
                                    self.file_queue.append(fname)
                                self.logger.info("%s: FileSaveDeque dumped %s packets to file %s", (self.name, len(dump_out), fname))
            elif self.allow_recover:
                recover_list = []
                for i in xrange(self.allow_recover):
                    fname = None
                    with self.file_lock:
                        if len(self.file_queue) > 0:
                            fname = self.file_queue.popleft()
                    if not fname: break
                    try:
                        rec_file = open(fname, 'rb')
                        recover_list = marshal.load(rec_file)
                    except Exception, ex:
                        self.logger.error("%s: FileSaveDeque fileread exception: %s \n %s", (self.name, repr(ex), traceback.format_exc()))
                    finally:
                        rec_file.close()
                        os.unlink(fname)
                    if recover_list:
                        with self.LOCK:
                            self.extend(recover_list)
                        self.logger.info("%s: FileSaveDeque read %s packets from file %s", (self.name, len(recover_list), fname))             
        except Exception, ex:
            self.logger.error("%s: FileSaveDeque fileread exception: %s \n %s", (self.name, repr(ex), traceback.format_exc()))
             
        
        
    
