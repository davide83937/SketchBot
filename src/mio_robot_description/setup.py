import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'mio_robot_description'

# Genera dinamicamente le risorse se presenti
resource_path = os.path.join('resource', package_name)
resource_files = [resource_path] if os.path.exists(resource_path) else []

setup(
    name=package_name,
    version='0.0.0',
    # Trova sia i moduli nella radice che in eventuali sottocartelle
    packages=find_packages(exclude=['test']),
    py_modules=['app', 'function', 'base_model', 'move_robot', 'check_pose'],
    # Mantiene visibili i file .py nella radice
    data_files=[
        ('share/ament_index/resource_index/packages', resource_files),
        ('share/' + package_name, ['package.xml']),

        # --- CARTELLE FONDAMENTALI PER MOVEIT E ROS 2 ---
        # Include tutti i file di launch (.launch.py)
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py') + glob('launch/*.py')),

        # Include i file URDF e Xacro del robot
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),

        # Include i file di configurazione SRDF / MoveIt / Controllers
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='davide',
    maintainer_email='davide@todo.todo',
    description='Pacchetto ROS 2 per mio_robot_description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # Se move_robot.py è nella radice:
            'move_robot = move_robot:main',
        ],
    },
)