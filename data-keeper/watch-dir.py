import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler
import os
import magic
import shutil
import pathlib
from datetime import datetime
import tarfile
import re


class StorageHandler(RegexMatchingEventHandler):
    def __init__(self, watch_dir):
        self.storage_dir = watch_dir
        self.watch_reg = (f"{self.storage_dir}/*")
        super().__init__([self.storage_dir])

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        
        # create uniq symlink based on must-gather name
        try:
            mg_root = r'.*(?P<mg_path>must-gather\.local\.\d+\/[a-z0-9\-]+)(\/|)$'
            mg_name = r'.*(?P<mg_name>must-gather\.local\.\d+)(\/|).*'
            re_mr = re.search(mg_root, event.src_path)
            if re_mr:
                re_nm = re.search(mg_name, event.src_path)
                if re_nm:
                    self.link_mustgather(event.src_path, re_nm.group('mg_name'))
        except Exception as e:
            logging.error(e)
            pass

        # # lookup for 'version' file on a valid must-gather
        # if os.path.isfile(event.src_path + "/version"):
        #     logging.info("Version found...")
        #     #self.link_mustgather(event.src_path, re_nm.group('mg_name'))
        #     return

    def link_mustgather(self, path, linkname):
        #symlink = f"00-{datetime.now().isoformat().replace(':','').split('.')[0]}"
        #dst_link = f"{self.storage_dir}/{symlink}"
        dst_link = f"{self.storage_dir}/00-{linkname}"
        logging.info(f"Creating symlink for must-gather {path} -> {dst_link}")
        try:
            os.symlink(path, dst_link)
        except FileExistsError:
            pass
        except:
            raise


class UploadHandler(RegexMatchingEventHandler):

    def __init__(self, watch_dir, storage_dir='/tmp'):
        self.watch_dir = watch_dir
        self.watch_reg = (f"{self.watch_dir}/*")
        super().__init__([self.watch_reg])
        self.storage_dir = storage_dir

    def on_created(self, event):
        self.process(event)

    def process(self, event):
        # print("UploadHandler() Processing")
        # print(event.src_path)
        # filename, ext = os.path.splitext(event.src_path)
        # print(filename, ext)

        # wait for file complete
        sleep_time = 10
        time.sleep(sleep_time)

        if os.path.isdir(event.src_path):
            fname = os.path.basename(event.src_path)
            logging.info(f"Moving directory [{fname}] to storage...")
            shutil.move(event.src_path, f'{self.storage_dir}/{fname}')
            return
        
        #print(magic.from_file(event.src_path, mime=True))
        if event.src_path.endswith('.tar.gz'):
            logging.info(f"Extracting tar.gz: {event.src_path}")
            with tarfile.open(event.src_path, "r:gz") as so:
                so.extractall(path=self.storage_dir)
            logging.info(f"Extract done to {self.storage_dir}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    path_pref = '/tmp/data'
    
    pathlib.Path(f'{path_pref}/storage').mkdir(parents=True, exist_ok=True)
    pathlib.Path(f'{path_pref}/uploads').mkdir(parents=True, exist_ok=True)
    
    path_upload = f'{path_pref}/uploads'
    path_storage = f'{path_pref}/storage'
    
    uploader_handler = UploadHandler(path_upload, storage_dir=path_storage)
    storage_handler = StorageHandler(path_storage)

    observer = Observer()
    observer.schedule(uploader_handler, path_upload, recursive=True)
    observer.schedule(storage_handler, path_storage, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
