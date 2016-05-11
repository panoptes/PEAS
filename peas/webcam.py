import os
import os.path
import sys
import shutil
import subprocess

from panoptes.utils import current_time
from panoptes.utils import process


class Webcam(process.PanProcess):

    """ Simple module to take a picture with the webcams

    This class will capture images from any webcam entry in the config file.
    The capturing is done on a loop, with defaults of 255 stacked images and
    a minute cadence.


    Note:
            All parameters are optional.

    Note:
            This is a port of Olivier's `SKYCAM_start_webcamloop` function
            in skycam.c

    Note:
            TODO: The images then have their flux measured and the gain and brightness
            adjusted accordingly. Images analysis is stored in the (mongo) database

    Args:
            webcam (dict):      Config options for the camera, required.
            frames (int):       Number of frames to capture per image. Default 255
            resolution (str):   Resolution for images. Default "1600x1200"
            brightness (str):   Initial camera brightness. Default "50%"
            gain (str):         Initial camera gain. Default "50%"
            delay (int):        Time to wait between captures. Default 60 (seconds)
    """

    def __init__(self, webcam, frames=255, resolution="1600x1200", brightness="50%", gain="50%"):
        super().__init__(name=webcam.get('name', 'WebCam'))

        self.webcam_dir = self.config['directories'].get('webcam', '/var/panoptes/webcams/')
        assert os.path.exists(self.webcam_dir), self.logger.warning(
            "Webcam directory must exist: {}".format(self.webcam_dir))

        self.logger.info("Creating webcams")

        # Lookup the webcams
        if webcam is None:
            err_msg = "No webcams to connect. Please check config.yaml and all appropriate ports"
            self.logger.warning(err_msg)

        self.webcam = webcam
        self.last_reading = None

        # Command for taking pics
        self.cmd = shutil.which('fswebcam')

        # Defaults
        self._timestamp = "%Y-%m-%d %H:%M:%S"
        self._thumbnail_resolution = '240x120'

        # Create the string for the params
        self.base_params = "-F {} -r {} --set brightness={} --set gain={} --jpeg 100 --timestamp \"{}\" ".format(
            frames, resolution, brightness, gain, self._timestamp)

    def step(self):
        """ Calls `capture` in a loop for an individual camera """
        self.capture()

    def capture(self):
        """ Capture an image from a webcam

        Given a webcam, this attempts to capture an image using the subprocess
        command. Also creates a thumbnail of the image

        Args:
            webcam (dict): Entry for the webcam. Example::
                {
                    'name': 'Pier West',
                    'port': '/dev/video0',
                    'params': {
                        'rotate': 270
                    },
                }

            The values for the `params` key will be passed directly to fswebcam
        """
        webcam = self.webcam

        assert isinstance(webcam, dict)
        self.logger.debug("Capturing image for {}...".format(webcam.get('name')))

        # Filename to save
        camera_name = webcam.get('port').split('/')[-1]

        # Create the directory for storing images
        webcam_dir = self.config['directories'].get('webcam')
        timestamp = current_time(flatten=True)
        date_dir = timestamp.split('T')[0]

        try:
            os.makedirs("{}/{}".format(webcam_dir, date_dir), exist_ok=True)
        except OSError as err:
            self.logger.warning("Cannot create new dir: {} \t {}".format(date_dir, err))

        # Output file names
        out_file = '{}/{}/{}_{}.jpeg'.format(webcam_dir, date_dir, camera_name, timestamp)

        # We also create a thumbnail and always link it to the same image
        # name so that it is always current.
        thumbnail_file = '{}/tn_{}.jpeg'.format(webcam_dir, camera_name)

        options = self.base_params
        if 'params' in webcam:
            for opt, val in webcam.get('params').items():
                options += "--{}={}".format(opt, val)

        # Assemble all the parameters
        params = " -d {} --title \"{}\" {} --save {} --scale {} {}".format(
            webcam.get('port'),
            webcam.get('name'),
            options,
            out_file,
            self._thumbnail_resolution,
            thumbnail_file
        )

        # Actually call the command.
        # NOTE: This is a blocking call (within this process). See `start_capturing`
        try:
            self.logger.debug("Webcam subproccess command: {} {}".format(self.cmd, params))
            with open(os.devnull, 'w') as devnull:
                retcode = subprocess.call(self.cmd + params, shell=True, stdout=devnull, stderr=devnull)

            self.last_reading = out_file
            if retcode < 0:
                self.logger.warning(
                    "Image captured terminated for {}. Return code: {} \t Error: {}".format(
                        webcam.get('name'),
                        retcode,
                        sys.stderr
                    )
                )
            else:
                self.logger.debug("Image captured for {}".format(webcam.get('name')))

                # Static files (always points to most recent)
                static_out_file = '{}/{}.jpeg'.format(webcam_dir, camera_name)

                # Symlink the latest image
                if os.path.lexists(static_out_file):
                    os.remove(static_out_file)

                os.symlink(out_file, static_out_file)

                return retcode
        except OSError as e:
            self.logger.warning("Execution failed:".format(e, file=sys.stderr))