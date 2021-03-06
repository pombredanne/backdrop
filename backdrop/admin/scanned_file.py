import hashlib
import os
from subprocess import Popen, PIPE


class VirusSignatureError(StandardError):

    def __init__(self, message):
        self.message = message


class ScannedFile(object):

    def __init__(self, file_object):
        self.file_object = file_object
        self._virus_signature = False
        self._file_path = '/tmp/{0}'.format(
            os.path.basename(self.file_object.filename))

    @property
    def has_virus_signature(self):
        self._save_file_to_disk()
        self._scan_file()
        self._clean_up()
        return self._virus_signature

    def _save_file_to_disk(self):
        self.file_object.save(self._file_path)

    def _scan_file(self):
        self._virus_signature = (self._virus_signature or
                                 self._clamscan(self._file_path))

    def _clamscan(self, filename):
        args = ['clamdscan', filename]
        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        _, stderrdata = proc.communicate()
        retcode = proc.returncode
        # 0 : No virus found.
        # 1 : Virus(es) found.
        # 2 : An error occured.
        if retcode == 0:
            return False
        elif retcode == 1:
            return True
        elif retcode == 2:
            raise SystemError('Error running the clamdscan virus scanner. '
                              'Stderr was "{}"'.format(stderrdata))

    def _clean_up(self):
        # Remove temporary file
        os.remove(self._file_path)
        # Reset stream position on file_object so that it can be read again
        self.file_object.seek(0)
