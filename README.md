# prefectbot 🤖
_💯 El robot prefecto_

Robot con la capacidad de seguir rutas pre-establecidas, encontrar puntos de control y realizar distintas tareas de monitoreo en tiempo real y de manear autonoma.

## 🤔 Como funciona:

El robot  tiene distintas **tareas**, semejantes a las que un _prefecto_ realizaria, y la capacidad de realizar estas tareas de manera autonoma buscando distintos marcadores.

Es importante mencionar que estas tareas pueden ser realizadas de manera manual si asi se desea pues el robot cuenta con una interfaz de monitoreo la cual funciona en tiempo real la cual da la capacidad de controlar las acciones de este mismo.

En una manera general el robot busca realizar la tarea de recorrer aulas y buscar maestros para luego registrar estas apariciones.

Esto, entonces, se divide en las siguientes tareas:

### 📝 Tarea: `Recorrido`

Durante esta tarea el robot:

* 🎦 Busca una linea utilizando un rango de colores
* 🔍 Busca un punto de control que denote la ubicacion de un salon, ya sea utilizando un codigo QR o un color distintivo.
* ➡️Al encontrar un punto de control, entonces, ejecutara la siguiente tarea asignada, en este caso la tarea `Reconocer`

### 📝 Tarea: `Reconocer`

Durante esta tarea el robot:
* ✋ Se detiene
* 🔍 Busca caras y las compara con las ya conocidas
* 📒 En caso de reconocer una cara se registrara el evento en una base de datos
* ⏪ Una vez finalizado volvera a la tarea anterior de `Recorrido`

## 💻 La interfaz de usuario

Como mencionamos anteriormente, el usuario tiene la capacidad de monitorear los eventos de el robot, ademas de ofrecerle la capacidad de tomar control de el funcionamiento de este mismo.

Para estas acciones ofrecemos la _interfaz de usuario_ la cual cuenta con:

* 🎦 Feed de video en tiempo real acompañado por anotaciones realizadas de el robot
* 🎮 Panel de control de movimiento de el robot
* 📒 Panel de control con los eventos registrados
