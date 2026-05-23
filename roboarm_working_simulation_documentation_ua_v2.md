# Роборука ROS 2 + MoveIt: робоча симуляція, структура та керування

Дата фіксації: 2026-05-23  
ROS 2: Humble  
Середовище: Docker-контейнер `roboarm_humble`  
Проєкт: `/ws/src/Roboarm`  
Робоча директорія збірки: `/ws`  
Поточний TCP / end-effector: `link_5`  
Базова система координат: `base_link`

---

## 1. Що вже працює

На поточному етапі симуляція роборуки працює стабільно. Піднята повна базова інфраструктура ROS 2 + MoveIt:

```text
Xacro / URDF модель
→ robot_state_publisher
→ TF-дерево
→ ros2_control fake hardware
→ joint_state_broadcaster
→ arm_trajectory_controller
→ MoveIt move_group
→ MoveIt Servo
→ RViz
→ Python-скрипти керування
→ GUI / arm_panel
```

Перевірено, що рука рухається у RViz через команди суглобів, через готову safe pose, через workspace-позиції та через MoveIt Servo по напрямках X/Y/Z.

Поточна система дозволяє:

```text
1. Запустити симуляцію роборуки.
2. Побачити модель у RViz.
3. Рухати руку через кути суглобів.
4. Перевіряти позицію TCP через TF.
5. Рухати TCP через MoveIt Servo по X/Y/Z.
6. Користуватись панеллю керування.
7. Додавати власні пози та змінювати параметри керування.
```

---

## 2. Загальна логіка роботи системи

У цій системі роборука не рухається напряму через переміщення ланок. Правильна логіка така: ми задаємо або кути суглобів, або бажану швидкість TCP, а ROS-система сама перетворює це на оновлення стану суглобів і TF.

Базовий ланцюжок руху:

```text
скрипт / GUI / панель керування
  ↓
команда на суглоби або Servo-команда
  ↓
MoveIt / MoveIt Servo / trajectory controller
  ↓
ros2_control fake hardware
  ↓
/joint_states
  ↓
robot_state_publisher
  ↓
/tf
  ↓
RViz показує нове положення моделі
```

Критичне правило:

```text
Якщо /joint_states змінюється — робот у ROS рухається.
Якщо /tf змінюється — кінематика перераховується.
Якщо print_ee_pose показує нову позицію link_5 — TCP реально змінився.
Якщо це все змінюється, але RViz не показує рух — проблема в налаштуванні RViz, а не в контролері.
```

---

## 3. Два режими керування

У поточній системі є два основні режими керування.

### 3.1. Joint control

У цьому режимі ми напряму задаємо кути всіх шести суглобів:

```text
joint_0
joint_1
joint_2
joint_3
joint_4
joint_5
```

Приклад:

```bash
ros2 run arm_tasks move_joints 0.0 0.8 0.6 -0.7 0.5 0.0
```

Цей режим потрібен для великих переміщень, переходів між робочими зонами, перевірки кінематики та задання готових робочих поз.

Ланцюжок роботи:

```text
move_joints.py
  ↓
/arm_trajectory_controller/follow_joint_trajectory
  ↓
joint_trajectory_controller
  ↓
ros2_control fake hardware
  ↓
/joint_states
  ↓
/tf
  ↓
RViz
```

### 3.2. Cartesian Servo control

У цьому режимі ми задаємо швидкість TCP по осях `base_link`:

```text
X+ / X-
Y+ / Y-
Z+ / Z-
```

Команда має тип:

```text
geometry_msgs/TwistStamped
```

Вона публікується в topic:

```text
/servo_node/delta_twist_cmds
```

MoveIt Servo перетворює цю Cartesian-швидкість на зміни суглобів і відправляє траєкторію в:

```text
/arm_trajectory_controller/joint_trajectory
```

Ланцюжок Servo:

```text
servo_step / servo_gui / arm_panel
  ↓
/servo_node/delta_twist_cmds
  ↓
servo_node
  ↓
/arm_trajectory_controller/joint_trajectory
  ↓
joint_trajectory_controller
  ↓
/joint_states
  ↓
/tf
  ↓
RViz
```

Важливе правило: Servo треба використовувати для малої доводки, а не як основний спосіб переміщення по всій робочій області. Великі рухи — через готові joint-позиції або MoveIt planning. Servo — для точної ручної корекції.

---

## 4. Кінематична структура робота

Поточне дерево ланок:

```text
world_link
  └── base_link
      └── link_0
          └── link_1
              └── link_2
                  └── link_3
                      └── link_4
                          └── link_5
```

Суглоби:

```text
world_to_base_joint fixed
joint_0
joint_1
joint_2
joint_3
joint_4
joint_5
```

Інженерне трактування:

```text
joint_0 — поворот усієї руки навколо вертикальної осі Z
joint_1 — плече
joint_2 — лікоть / основне згинання
joint_3 — добір кута у площині руки
joint_4 — орієнтаційний суглоб біля кінця руки
joint_5 — осьовий поворот TCP / кінцевої ланки
```

Для досягнення позиції TCP основними є:

```text
joint_0
joint_1
joint_2
joint_3
```

`joint_4` та `joint_5` на цьому етапі краще розглядати як орієнтаційні суглоби. Вони не повинні бути основним способом “дотягнутись” до точки.

---

## 5. Поточна робоча safe pose

Погана стартова поза — вертикально витягнута рука, де TCP був приблизно біля:

```text
x ≈ 0
z ≈ 1.28
```

У такій конфігурації Servo легко потрапляє в область сингулярності або близько до лімітів суглобів.

Поточна робоча safe pose:

```text
joint_0 = 0.0
joint_1 = 0.8
joint_2 = 0.6
joint_3 = -0.7
joint_4 = 0.5
joint_5 = 0.0
```

Команда:

```bash
ros2 run arm_tasks move_safe_home
```

Очікувана позиція TCP:

```text
frame: base_link -> link_5

x ≈ 0.849
y ≈ -0.024
z ≈ 0.753
roll  ≈ 0.5
pitch ≈ 0.7
yaw   ≈ 0.0
```

Ця поза використовується як основна стартова точка перед Servo та перед ручним керуванням.

---

## 6. Структура проєкту

Поточна структура:

```text
Roboarm/
├── arm_description/
├── arm_control/
├── arm_bringup/
├── arm_moveit_config/
├── arm_tasks/
└── docs/
```

---

## 7. Модуль arm_description

### Призначення

`arm_description` відповідає за опис робота. Тут знаходиться Xacro/URDF-модель: ланки, суглоби, геометрія, матеріали, інерції та ros2_control interface.

Основні файли:

```text
arm_description/urdf/arm.urdf.xacro
arm_description/urdf/links.xacro
arm_description/urdf/joints.xacro
arm_description/urdf/materials.xacro
arm_description/urdf/ros2_control.xacro
```

### Що де змінювати

Якщо треба змінити форму, розміри або візуальну геометрію ланок:

```text
arm_description/urdf/links.xacro
```

Якщо треба змінити осі суглобів, їхнє розташування або ліміти:

```text
arm_description/urdf/joints.xacro
```

Якщо треба змінити кольори або матеріали в RViz:

```text
arm_description/urdf/materials.xacro
```

Якщо треба змінити ros2_control interface:

```text
arm_description/urdf/ros2_control.xacro
```

Після зміни URDF/Xacro треба перебудувати проєкт і перезапустити backend:

```bash
cd /ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source /ws/install/setup.bash
```

---

## 8. Модуль arm_control

### Призначення

`arm_control` відповідає за конфігурацію `ros2_control`.

Основний файл:

```text
arm_control/config/controllers.yaml
```

У ньому задаються:

```text
controller_manager
joint_state_broadcaster
arm_trajectory_controller
список суглобів
command_interfaces
state_interfaces
частоти оновлення
обмеження контролера
```

Поточні активні контролери:

```text
joint_state_broadcaster
arm_trajectory_controller
```

Перевірка:

```bash
ros2 control list_controllers
```

Очікувано:

```text
joint_state_broadcaster   active
arm_trajectory_controller active
```

### joint_state_broadcaster

Публікує стан суглобів у:

```text
/joint_states
```

Цей topic читає `robot_state_publisher`. Якщо `/joint_states` не оновлюється, модель не буде рухатись у TF і RViz.

### arm_trajectory_controller

Приймає траєкторії суглобів.

Основні інтерфейси:

```text
/arm_trajectory_controller/follow_joint_trajectory
/arm_trajectory_controller/joint_trajectory
```

Через нього працюють:

```text
move_joints.py
move_safe_home.py
workspace_probe.py
MoveIt
MoveIt Servo
arm_panel.py
```

---

## 9. Модуль arm_bringup

### Призначення

`arm_bringup` відповідає за запуск базової симуляційної системи.

Основний launch-файл:

```text
arm_bringup/launch/full_fake.launch.py
```

Він піднімає:

```text
robot_state_publisher
ros2_control_node
joint_state_broadcaster
arm_trajectory_controller
move_group
```

Запуск backend:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 launch arm_bringup full_fake.launch.py
```

Цей термінал треба залишати відкритим.

---

## 10. Модуль arm_moveit_config

### Призначення

`arm_moveit_config` відповідає за MoveIt.

Основні файли:

```text
arm_moveit_config/config/arm.srdf
arm_moveit_config/config/kinematics.yaml
arm_moveit_config/config/joint_limits.yaml
arm_moveit_config/config/ompl_planning.yaml
arm_moveit_config/config/moveit_controllers.yaml
arm_moveit_config/config/servo.yaml
```

### arm.srdf

Описує MoveIt-групу:

```text
arm
```

Також тут можуть бути вимкнені зайві self-collision перевірки між сусідніми ланками. Це потрібно, щоб MoveIt не вважав нормальні стартові позиції collision-state.

### kinematics.yaml

Відповідає за IK solver. У майбутньому, коли буде керування через цільову TCP-позицію `x, y, z`, якість IK буде залежати від цього файлу.

### servo.yaml

Відповідає за MoveIt Servo.

Критичні параметри:

```yaml
move_group_name: arm
planning_frame: base_link
ee_frame_name: link_5
command_out_topic: /arm_trajectory_controller/joint_trajectory
cartesian_command_in_topic: /servo_node/delta_twist_cmds
```

Поточний робочий масштаб Servo:

```yaml
scale:
  linear: 0.30
  rotational: 0.30
  joint: 0.30

override_velocity_scaling_factor: 0.60
```

Саме ці значення зробили рух у RViz помітним і контрольованим.

Якщо рух занадто повільний:

```text
збільшити scale.linear
```

Якщо рух занадто різкий:

```text
зменшити scale.linear або override_velocity_scaling_factor
```

Рекомендований робочий діапазон:

```text
scale.linear: 0.15 ... 0.35
override_velocity_scaling_factor: 0.30 ... 0.70
```

Після зміни `servo.yaml` треба перезапустити Servo:

```bash
pkill -9 -f servo_node_main || true

ros2 launch arm_moveit_config servo.launch.py
```

---

## 11. Модуль arm_tasks

### Призначення

`arm_tasks` містить Python-інструменти для керування, тестування і діагностики.

Основні файли:

```text
move_joints.py
move_safe_home.py
print_ee_pose.py
workspace_probe.py
servo_probe.py
servo_step.py
servo_gui.py
arm_panel.py
```

### move_joints.py

Відправляє цільові кути суглобів у trajectory controller.

Приклад:

```bash
ros2 run arm_tasks move_joints 0.0 0.8 0.6 -0.7 0.5 0.0
```

Це базовий інструмент перевірки, що контролер працює.

### move_safe_home.py

Переводить руку у стабільну стартову позу.

Команда:

```bash
ros2 run arm_tasks move_safe_home
```

Поточна safe pose:

```text
[0.0, 0.8, 0.6, -0.7, 0.5, 0.0]
```

### print_ee_pose.py

Показує поточну позу TCP `link_5` відносно `base_link`.

Команда:

```bash
ros2 run arm_tasks print_ee_pose
```

Це головний інструмент числової перевірки. Якщо RViz візуально неочевидний, `print_ee_pose` показує, чи реально змінилась TCP-позиція.

### workspace_probe.py

Перевіряє робочу область через набір заздалегідь заданих joint-поз.

Команда:

```bash
ros2 run arm_tasks workspace_probe
```

Перевірені пози:

```text
front_mid
front_high
front_low
front_near
front_far
left_mid
right_mid
back_mid
left_low
right_low
home_end
```

Характерні результати:

```text
front_mid   x≈ 0.849   y≈-0.024   z≈0.753
front_high  x≈ 0.587   y≈-0.024   z≈1.078
front_low   x≈ 0.947   y≈-0.024   z≈0.454
left_mid    x≈ 0.025   y≈ 0.849   z≈0.753
right_mid   x≈-0.022   y≈-0.849   z≈0.753
back_mid    x≈-0.849   y≈ 0.027   z≈0.753
```

Висновок: `joint_0` правильно обертає робочу область навколо бази, а `joint_1..joint_3` формують радіус і висоту.

### servo_probe.py

Перевіряє, чи MoveIt Servo реально генерує `joint_trajectory`.

Команда:

```bash
ros2 run arm_tasks servo_probe
```

Правильний результат:

```text
trajectory messages > 0
last servo status = 0
joint delta != 0
```

Цей тест довів, що Servo працює, якщо публікувати `TwistStamped` з реальним timestamp.

### servo_step.py

Дає коротку Servo-команду по X/Y/Z з правильним timestamp.

Приклади:

```bash
ros2 run arm_tasks servo_step --vx 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vx -0.03 --duration 2.0

ros2 run arm_tasks servo_step --vy 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vy -0.03 --duration 2.0

ros2 run arm_tasks servo_step --vz 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vz -0.03 --duration 2.0
```

Це основний CLI-інструмент для перевірки Servo. Не треба використовувати `ros2 topic pub --once` для Servo-діагностики, бо там часто йде `stamp=0`, і такий тест може бути неправильним.

### servo_gui.py

Просте GUI для ручного Cartesian-керування через Servo.

Публікує команди в:

```text
/servo_node/delta_twist_cmds
```

Рекомендована швидкість:

```text
0.015 ... 0.050
```

### arm_panel.py

Основна панель керування роборукою.

Має поєднувати:

```text
готові joint-позиції
Servo X/Y/Z
Start Servo
STOP
швидкість
статус Servo
```

Правильна концепція:

```text
великі переміщення — через готові joint-позиції
мала доводка — через Servo
```

---

## 12. Повний запуск системи

### 12.1. Увійти в контейнер

На хості:

```bash
docker ps
```

Якщо контейнер запущений:

```bash
docker exec -it roboarm_humble bash
```

Якщо контейнер зупинений:

```bash
docker start roboarm_humble
docker exec -it roboarm_humble bash
```

### 12.2. Очистити старі процеси

```bash
pkill -9 -f "ros2 launch" || true
pkill -9 -f "launch_ros" || true
pkill -9 -f "ros2_control_node" || true
pkill -9 -f "robot_state_publisher" || true
pkill -9 -f "move_group" || true
pkill -9 -f "servo_node_main" || true
pkill -9 -f "servo_gui" || true
pkill -9 -f "arm_panel" || true
pkill -9 -f "rviz2" || true
pkill -9 -f "spawner" || true

ros2 daemon stop
ros2 daemon start
sleep 2
```

### 12.3. Зібрати проєкт

```bash
cd /ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source /ws/install/setup.bash
```

### 12.4. Запустити backend

Термінал 1:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 launch arm_bringup full_fake.launch.py
```

### 12.5. Перевірити backend

Термінал 2:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 node list
ros2 control list_controllers
ros2 topic echo /joint_states --once
```

Очікувано:

```text
joint_state_broadcaster active
arm_trajectory_controller active
```

### 12.6. Запустити RViz

Термінал 3:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

rviz2
```

У RViz:

```text
Fixed Frame: base_link
Add → RobotModel
Add → TF
RobotModel → Description Topic: /robot_description
```

### 12.7. Перевести руку в safe home

Термінал 2:

```bash
ros2 run arm_tasks move_safe_home
ros2 run arm_tasks print_ee_pose
```

### 12.8. Запустити Servo

Термінал 4:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 launch arm_moveit_config servo.launch.py
```

Термінал 2:

```bash
ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
```

Перевірка параметрів Servo:

```bash
ros2 param get /servo_node moveit_servo.move_group_name
ros2 param get /servo_node moveit_servo.ee_frame_name
ros2 param get /servo_node moveit_servo.planning_frame
ros2 param get /servo_node moveit_servo.command_out_topic
ros2 param get /servo_node moveit_servo.scale.linear
ros2 param get /servo_node moveit_servo.override_velocity_scaling_factor
```

Очікувано:

```text
arm
link_5
base_link
/arm_trajectory_controller/joint_trajectory
0.30
0.60
```

---

## 13. Керування роботом

### 13.1. Через готові joint-позиції

Safe home:

```bash
ros2 run arm_tasks move_safe_home
```

Поворот вліво:

```bash
ros2 run arm_tasks move_joints 1.57 0.8 0.6 -0.7 0.5 0.0
```

Повернення вперед:

```bash
ros2 run arm_tasks move_joints 0.0 0.8 0.6 -0.7 0.5 0.0
```

### 13.2. Через Servo CLI

Перед Servo:

```bash
ros2 run arm_tasks move_safe_home
ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
```

Рух по X:

```bash
ros2 run arm_tasks servo_step --vx 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vx -0.03 --duration 2.0
```

Рух по Y:

```bash
ros2 run arm_tasks servo_step --vy 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vy -0.03 --duration 2.0
```

Рух по Z:

```bash
ros2 run arm_tasks servo_step --vz 0.03 --duration 2.0
ros2 run arm_tasks servo_step --vz -0.03 --duration 2.0
```

Після кожного тесту:

```bash
ros2 run arm_tasks print_ee_pose
ros2 topic echo /servo_node/status --once
```

Очікуваний статус:

```text
data: 0
```

### 13.3. Через arm_panel

Запуск:

```bash
ros2 run arm_tasks arm_panel
```

Правильна логіка використання:

```text
1. Натиснути Safe Home.
2. Для великих переміщень використовувати Front / Left / Right / Back / High / Low.
3. Натиснути Start Servo.
4. Для малої доводки використовувати X+/X-/Y+/Y-/Z+/Z-.
5. Для зупинки натиснути STOP.
```

---

## 14. Як змінювати керування під себе

### 14.1. Змінити safe pose

Файл:

```text
arm_tasks/arm_tasks/move_safe_home.py
```

Змінити масив:

```python
SAFE_HOME = [
    0.0,
    0.8,
    0.6,
    -0.7,
    0.5,
    0.0,
]
```

Після зміни:

```bash
cd /ws
colcon build --symlink-install
source /ws/install/setup.bash
```

### 14.2. Додати нову готову позу

Файл:

```text
arm_tasks/arm_tasks/arm_panel.py
```

У словник `POSES` додати:

```python
"New Pose": [joint_0, joint_1, joint_2, joint_3, joint_4, joint_5],
```

Перед додаванням у панель позу треба перевірити:

```bash
ros2 run arm_tasks move_joints ...
ros2 run arm_tasks print_ee_pose
```

### 14.3. Змінити швидкість Servo

Файл:

```text
arm_moveit_config/config/servo.yaml
```

Основні параметри:

```yaml
scale:
  linear: 0.30
  rotational: 0.30
  joint: 0.30

override_velocity_scaling_factor: 0.60
```

Якщо рух занадто повільний — збільшити `scale.linear`.

Якщо рух занадто різкий — зменшити `scale.linear` або `override_velocity_scaling_factor`.

Після зміни треба перезапустити Servo:

```bash
pkill -9 -f servo_node_main || true
ros2 launch arm_moveit_config servo.launch.py
```

### 14.4. Змінити TCP

Поточний TCP:

```text
link_5
```

Коли буде додано грипер, TCP треба буде змінити на реальний кінцевий frame, наприклад:

```text
tool0
gripper_tcp
```

Місця, де це треба змінити:

```text
arm_moveit_config/config/servo.yaml
arm_moveit_config/config/arm.srdf
arm_tasks/arm_tasks/print_ee_pose.py
інші скрипти, де явно використано link_5
```

---

## 15. Діагностика

### 15.1. Перевірити backend

```bash
ros2 node list
ros2 control list_controllers
```

Очікувано:

```text
joint_state_broadcaster active
arm_trajectory_controller active
```

### 15.2. Перевірити joint states

```bash
ros2 topic echo /joint_states --once
```

Якщо `/joint_states` не оновлюється, TF і RViz не покажуть нового положення руки.

### 15.3. Перевірити TF

```bash
ros2 run arm_tasks print_ee_pose
```

або:

```bash
ros2 run tf2_ros tf2_echo base_link link_5
```

Якщо TF змінюється, але RViz не показує рух, проблема у RViz-конфігурації.

### 15.4. Перевірити Servo

```bash
ros2 node list | grep servo
ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
ros2 topic echo /servo_node/status --once
```

Очікуваний статус:

```text
data: 0
```

### 15.5. Якщо Servo не рухає

Не використовувати для основної діагностики:

```bash
ros2 topic pub --once ...
```

Краще:

```bash
ros2 run arm_tasks servo_probe
```

або:

```bash
ros2 run arm_tasks servo_step --vx 0.03 --duration 2.0
```

Причина: Servo потребує потоку `TwistStamped` з актуальним timestamp.

---

## 16. Поточний робочий baseline

Працює:

```text
URDF/Xacro модель
robot_state_publisher
TF
ros2_control fake hardware
joint_state_broadcaster
arm_trajectory_controller
MoveIt move_group
RViz visualization
move_joints
move_safe_home
workspace_probe
servo_probe
servo_step
MoveIt Servo X/Y/Z
arm_panel
```

Поточна робоча логіка керування:

```text
1. Великі переміщення — через joint poses або MoveIt planning.
2. Мала ручна доводка — через MoveIt Servo.
3. Сирі topic-команди — тільки для діагностики.
4. Перед Servo бажано переходити у safe_home.
5. Основний числовий контроль — через print_ee_pose.
```

---

---

## 17. Docker-середовище і де саме все запускати

Цей проєкт зручно запускати в Docker, бо ROS 2, MoveIt, ros2_control, RViz і Python GUI мають багато системних залежностей. Правильна модель така:

```text
host OS
  ↓
Docker container: roboarm_humble
  ↓
workspace: /ws
  ↓
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash
  ↓
запуск backend / RViz / Servo / GUI
```

Важливо не плутати, де виконуються команди:

```text
На host-машині:
  docker build
  docker run
  docker start
  docker exec

Всередині контейнера:
  colcon build
  ros2 launch
  ros2 run
  rviz2
  ros2 topic / service / control
```

Усі ROS-команди для цього проєкту треба виконувати всередині контейнера `roboarm_humble`, якщо спеціально не налаштовано інший ROS 2 environment на host-системі.

---

## 18. Рекомендована структура Docker-файлів у репозиторії

Рекомендовано додати в проєкт окрему директорію:

```text
Roboarm/
├── docker/
│   ├── Dockerfile.humble
│   ├── run_linux_x11.sh
│   └── enter.sh
```

Призначення файлів:

```text
Dockerfile.humble
  Описує образ з ROS 2 Humble, MoveIt, ros2_control, RViz, PyQt5 і dev-tools.

run_linux_x11.sh
  Запускає контейнер з підтримкою GUI через X11 на Linux / WSLg-compatible середовищі.

enter.sh
  Відкриває новий термінал всередині вже запущеного контейнера.
```

---

## 19. Dockerfile для ROS 2 Humble + MoveIt + RViz + GUI

Файл:

```text
Roboarm/docker/Dockerfile.humble
```

Вміст:

```dockerfile
FROM osrf/ros:humble-desktop-full

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    nano \
    wget \
    curl \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    python3-pyqt5 \
    python3-tk \
    ros-humble-moveit \
    ros-humble-moveit-servo \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-robot-state-publisher \
    ros-humble-xacro \
    ros-humble-tf2-tools \
    ros-humble-rviz2 \
    ros-humble-controller-manager \
    ros-humble-joint-trajectory-controller \
    ros-humble-joint-state-broadcaster \
    ros-humble-control-msgs \
    ros-humble-trajectory-msgs \
    ros-humble-geometry-msgs \
    ros-humble-sensor-msgs \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init 2>/dev/null || true
RUN rosdep update || true

WORKDIR /ws

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi" >> /root/.bashrc

CMD ["bash"]
```

Цей Dockerfile створює dev-середовище, в якому можна збирати та запускати поточний проєкт.

---

## 20. Збірка Docker-образу

Команда виконується на host-машині, не всередині контейнера.

З директорії репозиторію:

```bash
cd /path/to/Roboarm

docker build \
  -f docker/Dockerfile.humble \
  -t roboarm_humble:dev \
  .
```

Після успішної збірки перевірити образ:

```bash
docker images | grep roboarm_humble
```

Очікувано:

```text
roboarm_humble   dev
```

---

## 21. Запуск контейнера на Linux з X11 GUI

Файл:

```text
Roboarm/docker/run_linux_x11.sh
```

Вміст:

```bash
#!/usr/bin/env bash
set -e

xhost +local:docker >/dev/null 2>&1 || true

docker run -it \
  --name roboarm_humble \
  --net=host \
  --ipc=host \
  --privileged \
  -e DISPLAY=${DISPLAY} \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $(pwd):/ws/src/Roboarm \
  roboarm_humble:dev \
  bash
```

Зробити файл виконуваним:

```bash
chmod +x docker/run_linux_x11.sh
```

Запуск:

```bash
cd /path/to/Roboarm
./docker/run_linux_x11.sh
```

Після входу в контейнер проєкт буде доступний тут:

```text
/ws/src/Roboarm
```

Збирати треба з `/ws`:

```bash
cd /ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source /ws/install/setup.bash
```

---

## 22. Вхід у вже запущений контейнер

Файл:

```text
Roboarm/docker/enter.sh
```

Вміст:

```bash
#!/usr/bin/env bash
set -e

docker exec -it roboarm_humble bash
```

Зробити файл виконуваним:

```bash
chmod +x docker/enter.sh
```

Використання:

```bash
./docker/enter.sh
```

Цю команду треба використовувати для відкриття додаткових терміналів. Наприклад:

```text
Термінал 1 — backend
Термінал 2 — діагностика і команди
Термінал 3 — RViz
Термінал 4 — Servo
Термінал 5 — arm_panel
```

---

## 23. Якщо контейнер уже існує

Якщо контейнер був створений раніше, повторний `docker run --name roboarm_humble ...` не спрацює, бо ім’я вже зайняте.

Тоді запускати так:

```bash
docker start roboarm_humble
docker exec -it roboarm_humble bash
```

Якщо треба повністю видалити старий контейнер:

```bash
docker rm -f roboarm_humble
```

Після цього можна знову виконати:

```bash
./docker/run_linux_x11.sh
```

---

## 24. Де запускати конкретні частини системи

Правильний розподіл по терміналах:

```text
HOST terminal:
  docker start / docker exec / docker build

CONTAINER terminal 1:
  ros2 launch arm_bringup full_fake.launch.py

CONTAINER terminal 2:
  ros2 node list
  ros2 control list_controllers
  ros2 run arm_tasks move_safe_home
  ros2 run arm_tasks print_ee_pose
  ros2 run arm_tasks servo_step ...

CONTAINER terminal 3:
  rviz2

CONTAINER terminal 4:
  ros2 launch arm_moveit_config servo.launch.py

CONTAINER terminal 5:
  ros2 run arm_tasks arm_panel
```

Головне правило: `ros2 launch`, `ros2 run`, `rviz2`, `colcon build` виконуються всередині контейнера.

---

## 25. Повний запуск з Docker після перезавантаження комп’ютера

На host-машині:

```bash
docker start roboarm_humble
docker exec -it roboarm_humble bash
```

Всередині контейнера, термінал 1:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 launch arm_bringup full_fake.launch.py
```

Новий host-термінал:

```bash
docker exec -it roboarm_humble bash
```

Всередині контейнера, термінал 2:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 control list_controllers
ros2 run arm_tasks move_safe_home
ros2 run arm_tasks print_ee_pose
```

Новий host-термінал:

```bash
docker exec -it roboarm_humble bash
```

Всередині контейнера, термінал 3:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

rviz2
```

Новий host-термінал:

```bash
docker exec -it roboarm_humble bash
```

Всередині контейнера, термінал 4:

```bash
cd /ws
source /opt/ros/humble/setup.bash
source /ws/install/setup.bash

ros2 launch arm_moveit_config servo.launch.py
```

У терміналі 2 запустити Servo:

```bash
ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
```

Після цього можна запускати панель:

```bash
ros2 run arm_tasks arm_panel
```

---

## 26. Якщо RViz або GUI не відкривається з Docker

Найчастіша причина — контейнер не має доступу до графічного сервера host-системи.

Для Linux/X11 перевірити:

```bash
echo $DISPLAY
xhost +local:docker
```

Потім перезапустити контейнер через `run_linux_x11.sh`.

Якщо використовується Windows + WSLg, зазвичай GUI працює через WSLg автоматично, але контейнер треба запускати з правильним `DISPLAY` і volume для X11/Wayland залежно від конфігурації. У цьому проєкті найпростіший робочий варіант — запускати Docker з Linux/WSL shell, а всі ROS-команди виконувати всередині контейнера.

Якщо RViz запускається, але модель не видно:

```text
Fixed Frame: base_link
RobotModel → Description Topic: /robot_description
TF display увімкнений
```

Якщо RViz не показує рух, але `print_ee_pose` змінюється, проблема не в ROS-керуванні, а в RViz-конфігурації.

---

## 27. Мінімальний чекліст запуску

```text
1. Host:
   docker start roboarm_humble

2. Host:
   docker exec -it roboarm_humble bash

3. Container:
   cd /ws
   source /opt/ros/humble/setup.bash
   source /ws/install/setup.bash
   ros2 launch arm_bringup full_fake.launch.py

4. Новий container terminal:
   ros2 control list_controllers
   ros2 run arm_tasks move_safe_home
   ros2 run arm_tasks print_ee_pose

5. Новий container terminal:
   rviz2

6. Новий container terminal:
   ros2 launch arm_moveit_config servo.launch.py

7. Container command terminal:
   ros2 service call /servo_node/start_servo std_srvs/srv/Trigger {}
   ros2 run arm_tasks servo_step --vx 0.03 --duration 2.0

8. Для GUI:
   ros2 run arm_tasks arm_panel
```

---

