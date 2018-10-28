from setuptools import setup

setup(
    name="let-there-be-light",
    options={
        'build_apps': {
            'include_patterns': [
                'data/**',
                'config.prc',
            ],
            'gui_apps': {
                'run_game': 'run_game.py',
            },
            #'log_filename': '$USER_APPDATA/Let There Be Light/output.log',
            'log_filename': '$USER_APPDATA/let-there-be-light.log',
            'log_append': False,
            'plugins': [
                'pandagl',
                'p3openal_audio',
                'p3fmod_audio',
            ],
            'platforms': [
                'manylinux1_x86_64',
                'macosx_10_6_x86_64',
                'win_amd64',
            ],
        }
    }
)
