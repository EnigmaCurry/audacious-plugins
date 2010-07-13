from setuptools import setup

setup(name='AudaciousDynamicPlaylist',
      version="0.1",
      description="A tool to monitor a directory for new audio files and feed the audacious playlist with them",
      author='Ryan McGuire',
      author_email='ryan@enigmacurry.com',
      url='http://www.enigmacurry.com',
      license='MIT',
      packages=["ec_audacious"],
      install_requires =['pyinotify']
      )
