# README

Este proyecto es un servicio (API) en FastAPI para gestión de canales y miembros, con persistencia en MongoDB y mensajería de eventos vía RabbitMQ.

- Maximiliano Sepúlveda - ROL: 201973536-5
- Felipe Mellado - ROL: 201973525-K
- Cristopher Fuentes Llantén - ROL: 201973598-5

## REQUERIMIENTOS

- Docker 28+
- Docker Compose 2.40+
- Python 3.13

## IMAGEN DOCKER EN GHCR

Cada vez que se hace un commit a la rama `docker-image`, se construye y publica una nueva imagen Docker en GitHub Container Registry (GHCR).

Para descargar la imagen más reciente:

```bash
docker pull ghcr.io/moxwel/utfsm-arquisw-tareafinal:latest
```

Esta imagen se utiliza en el archivo `docker-compose.image.yml` para levantar los servicios, y en el archivo `kube-deployment.yml` para despliegue en Kubernetes.

## INSTRUCCIONES DE USO

### Paso 0: Verificar/ajustar variables de entorno (.env)

Archivo `.env` (valores por defecto):

```env
MONGO_URL=mongodb://mongo:27017
MONGO_DB_NAME=channel_service_db

RABBITMQ_URL=amqp://guest:guest@rabbitmq/
RABBITMQ_MAIN_EXCHANGE=channel_service_exchange
RABBITMQ_MAIN_QUEUE=channel_service_queue
RABBITMQ_DLX=dlx_exchange
RABBITMQ_DLQ=dlq_queue

RABBITMQ_MAX_RETRIES=20
RABBITMQ_RETRY_DELAY=3
```

- `MONGO_URL`: URL de conexión a MongoDB.
- `MONGO_DB_NAME`: Nombre de la base de datos en MongoDB.

- `RABBITMQ_URL`: URL de conexión a RabbitMQ.
- `RABBITMQ_MAIN_EXCHANGE`: Nombre del exchange principal.
- `RABBITMQ_MAIN_QUEUE`: Nombre de la cola principal.
- `RABBITMQ_DLX`: Nombre del exchange de dead-letter.
- `RABBITMQ_DLQ`: Nombre de la cola de dead-letter.

- `RABBITMQ_MAX_RETRIES`: Máximo número de reintentos para publicar
- `RABBITMQ_RETRY_DELAY`: Retardo (segundos) entre reintentos.

### Paso 1: Construir y levantar los servicios con Docker

```bash
docker compose -f docker-compose.image.yml up --build
```

> [!WARNING]
> Utilizar `docker compose up --build` (sin `-f`) esta pensado para entorno de desarrollo ya que se aplica el archivo `docker-compose.override.yml`. Asegurese de usar el archivo correcto en producción.

Esto levanta:
- `api` en el puerto 8000
- `mongo` en el puerto 27017
- `rabbitmq` en los puertos 5672 (AMQP) y 15672 (UI)

Para detener y borrar volúmenes:

```bash
docker compose down -v
```

### Paso 2: Verificar que todo esté corriendo

- **API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **RabbitMQ Management UI**: [http://localhost:15672](http://localhost:15672)
  - Usuario: `guest`
  - Clave: `guest`

La API intentará conectarse a RabbitMQ antes de iniciar el servidor. Reintentará `RABBITMQ_MAX_RETRIES` veces con un retardo de `RABBITMQ_RETRY_DELAY` segundos. **Si falla, el servicio no arrancará.**

### Paso 3: Probar flujo básico

- Crear, listar y eliminar canales desde la API (ver `/docs`).
- Al crear/eliminar, el servicio publica eventos en RabbitMQ (por ejemplo, `channel.created` / `channel.deleted`).
- Revise la cola/intercambio configurados en RabbitMQ para validar los mensajes.

## DESPLIEGUE EN KUBERNETES

El despliegue en un cluster de Kubernetes se puede realizar utilizando el archivo `kube-deployment.yml`. Asegúrese de tener un clúster de Kubernetes configurado y `kubectl` instalado.

> [!NOTE]
> Para un cluster local, se recomienda usar [Kind](https://kind.sigs.k8s.io/) con Docker, ya que se puede simular un cluster con multiples nodos fácilmente.

Para desplegar el servicio:

```bash
kubectl apply -f kube-deployment.yml
```

Los elementos desplegados incluyen:
- **MongoDB**: Un `Deployment` con 1 réplica, un `Service` de tipo `ClusterIP` y un `PersistentVolumeClaim` para la persistencia de datos.
- **RabbitMQ**: Un `Deployment` con 1 réplica y un `Service` de tipo `ClusterIP`.
- **API (FastAPI)**: Un `Deployment` con 3 réplicas, un `Service` de tipo `LoadBalancer` para exponer la API externamente, y un `ConfigMap` para la configuración.

### Verificar el despliegue

Para verificar el estado de todos los recursos desplegados:

```bash
kubectl get all
```

### Acceder al servicio

El servicio de la API se expone a través de un `LoadBalancer`. Para obtener la IP externa y acceder a la API:

1.  Obtén la IP externa del servicio:

    ```bash
    kubectl get service channel-api-service
    ```

2.  Busca la `EXTERNAL-IP` en la salida. Una vez que esté disponible, puedes acceder a la documentación de la API en `http://<EXTERNAL-IP>:8000/docs`.

> [!NOTE]
> Si se esta usando un clúster local (como Kind), es posible que el `EXTERNAL-IP` sea una IP interna de Docker. Para el caso de Kind, `LoadBalancer` causa que docker exponga el puerto del servicio en localhost. Entonces, considera `EXTERNAL-IP` como `localhost` y accede a la API en `http://localhost:8000/docs`.


### Limpiar el despliegue

Para eliminar todos los recursos creados en Kubernetes:

```bash
kubectl delete -f kube-deployment.yml
```
