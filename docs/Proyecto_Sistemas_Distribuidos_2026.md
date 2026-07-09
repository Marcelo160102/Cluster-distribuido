## **Proyecto: Implementación de un Clúster Distribuido con Replicación de Datos** 

## **1. Introducción** 

Los sistemas distribuidos constituyen una de las áreas más importantes de la informática moderna, ya que permiten que múltiples computadoras o nodos trabajen de manera coordinada para ofrecer servicios confiables, escalables y tolerantes a fallos. Actualmente, gran parte de las aplicaciones utilizadas en entornos empresariales, plataformas web, servicios en la nube y centros de datos se basan en arquitecturas distribuidas que permiten compartir recursos, procesar grandes volúmenes de información y garantizar la continuidad del servicio incluso ante fallos de hardware o software. 

Uno de los principales desafíos en este tipo de sistemas es mantener la consistencia y disponibilidad de la información cuando esta se encuentra distribuida en varios nodos. Para solucionar este problema se emplean técnicas como la replicación de datos, que consiste en almacenar copias de la información en diferentes servidores, permitiendo que el sistema continúe funcionando aun cuando alguno de los nodos deje de estar disponible. Asimismo, es necesario contar con mecanismos de consenso que permitan coordinar las decisiones entre los nodos participantes, garantizando que todos mantengan una visión coherente del estado del sistema. 

En este proyecto, los estudiantes desarrollarán un pequeño clúster distribuido compuesto por tres nodos interconectados capaces de intercambiar información y mantener réplicas consistentes de los datos. Además, se implementará un mecanismo básico de consenso o elección de líder que permita coordinar las operaciones del sistema y gestionar situaciones de fallo. A través de este desarrollo, los estudiantes podrán comprender de forma práctica conceptos fundamentales de los sistemas distribuidos, tales como replicación, consistencia, tolerancia a fallos, coordinación entre nodos y alta disponibilidad, aplicando los conocimientos adquiridos durante el curso en un escenario similar a los utilizados en entornos reales. 

## **2. Objetivos** 

Objetivo General: 

- Desarrollar un prototipo de sistema distribuido que implemente replicación de datos y un mecanismo básico de consenso entre nodos. 

Objetivos Específicos: 

- Diseñar una arquitectura distribuida basada en múltiples nodos. 

- Implementar la replicación de información entre nodos. 

- Implementar un mecanismo básico de consenso o elección de líder. 

- Evaluar el comportamiento del sistema ante la caída de un nodo. 

## **3. Alcance** 

El sistema deberá estar conformado por tres nodos conectados mediante red local o contenedores Docker. Cada nodo deberá almacenar información, replicar cambios, participar en un proceso de consenso y continuar operando cuando uno de los nodos deje de estar disponible. 

## **4. Desarrollo** 

El proyecto deberá implementar un clúster distribuido compuesto por tres nodos capaces de intercambiar información y coordinar sus operaciones. 

## **4.1 Arquitectura del Sistema** 

Los estudiantes deberán diseñar e implementar una arquitectura distribuida conformada por tres nodos conectados mediante red local o contenedores Docker. 

Se deberá presentar: 

- Diagrama de arquitectura del clúster. 

- Descripción de los componentes de cada nodo. 

- Descripción de los mensajes intercambiados entre nodos. 

- Identificación del nodo líder y nodos seguidores (si aplica). 

**Herramientas sugeridas:** Docker, Docker Compose, Python, Java, Node.js o Go. 

## **4.2 Replicación de Datos** 

Se deberá implementar un mecanismo de replicación que permita que la información almacenada en un nodo sea copiada automáticamente a los demás nodos del clúster. 

Se deberá demostrar: 

- Creación de registros. 

- Actualización de registros. 

- Sincronización correcta entre los nodos. 

- Consistencia de la información replicada. 

#### **Opciones recomendadas:** 

- Replicación Maestro-Esclavo (Primary-Replica). 

- Replicación Activa entre nodos. 

- Base de datos distribuida simple utilizando archivos JSON o SQLite. 

## **4.3 Mecanismo de Consenso o Elección de Líder** 

El sistema deberá implementar un mecanismo básico que permita seleccionar automáticamente un nodo líder responsable de coordinar determinadas operaciones. 

Se deberá demostrar: 

- Selección inicial del líder. 

- Detección de la caída del líder. 

- Elección automática de un nuevo líder. 

- Continuidad del servicio después del fallo. 

## **Algoritmos recomendados:** 

- Bully Algorithm. 

- Ring Election Algorithm. 

## **4.4 Pruebas de Funcionamiento** 

Los estudiantes deberán realizar pruebas que evidencien el correcto funcionamiento del sistema distribuido. 

Como mínimo deberán demostrar: 

1. Replicación exitosa de información entre nodos. 

2. Sincronización correcta de los datos replicados. 

3. Desconexión o apagado de un nodo. 

4. Elección automática de un nuevo líder (si aplica). 

5. Continuidad del servicio con los nodos restantes. 

Se deberán incluir capturas de pantalla o evidencias de las pruebas realizadas. 

## **5. Entregables** 

|**N.°**|**Entregable**|**Descripción**|
|---|---|---|
|1|Informe técnico|Documento final del proyecto con introducción, objetivos,<br>arquitectura, implementación, pruebas y conclusiones (máximo 15<br>páginas).|
|2|Código fuente<br>documentado|Código desarrollado para la implementación del clúster,<br>incluyendo comentarios y guía básica de ejecución.|
|3|Diagrama de<br>arquitectura|Representación gráfica de los nodos, las comunicaciones y el<br>mecanismo de replicación implementado.|
|4|Video demostrativo|Video de máximo 10 minutos mostrando el funcionamiento del<br>sistema, la replicación de datos y la tolerancia a fallos.|
|5|Presentación final|Exposición del proyecto donde se describa la solución desarrollada,<br>resultados obtenidos y lecciones aprendidas.|



## **6. Criterios de Evaluación** 

Diseño de arquitectura: 20% Replicación: 30% Consenso/Líder: 25% Pruebas y demostración: 15% Documentación y presentación: 10% 

