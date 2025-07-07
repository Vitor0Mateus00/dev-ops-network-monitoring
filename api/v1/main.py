import json
import os

from fastapi import FastAPI, HTTPException
import mysql.connector
import requests

from api.v1.models import TargetModel

app = FastAPI()

TARGETS_FILE = "/etc/prometheus/blackbox-targets.json"

MYSQL_CONFIG = {
    "host": "mysql",
    "user": "grafana",
    "password": "grafana",
    "database": "monitoring",
}

PROMETHEUS_URL = "http://prometheus:9090/api/v1/query"

targets = ["google.com", "youtube.com", "rnp.br"]


@app.on_event("startup")
async def startup_event():
    build_targets_json()
    print("Arquivo de targets criado e Prometheus recarregado.")


@app.get("/")
def main():
    return {"message": "API de targets de blackbox!"}


@app.get("/blackbox/targets")
def blackbox_targets():
    return {"targets": targets}


@app.post("/blackbox/add-target")
def add_blackbox_targets(data: TargetModel):
    new_target = data.target.strip().lower()
    if new_target in targets:
        raise HTTPException(status_code=400, detail="Target já existe.")
    targets.append(new_target)
    build_targets_json()
    return {"message": f"Target adicionado: {new_target}"}


@app.delete("/blackbox/delete-target")
def remove_blackbox_targets(data: TargetModel):
    target_to_remove = data.target.strip().lower()
    if target_to_remove not in targets:
        raise HTTPException(status_code=404, detail="Target não encontrado.")
    targets.remove(target_to_remove)
    build_targets_json()
    return {"message": f"Target removido: {target_to_remove}"}


def build_targets_json():
    targets_data = [{
        "labels": {},
        "targets": targets
    }]
    os.makedirs(os.path.dirname(TARGETS_FILE), exist_ok=True)

    try:
        with open(TARGETS_FILE, "w") as f:
            json.dump(targets_data, f, indent=2)
        os.system("curl -X POST http://prometheus:9090/-/reload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def query_prometheus(query):
    print(f"Rodando query: {query}")
    r = requests.get(PROMETHEUS_URL, params={"query": query})
    r.raise_for_status()
    data = r.json()
    print("Resposta:", data)
    return data


def save_ping_results(conn):
    cursor = conn.cursor()
    for target in targets:
        rtt_query = f'probe_icmp_rtt_seconds{{target="{target}"}}'
        loss_query = f'probe_icmp_loss{{target="{target}"}}'

        rtt_resp = query_prometheus(rtt_query)
        loss_resp = query_prometheus(loss_query)

        rtt_ms = None
        packet_loss = None

        if rtt_resp["data"]["result"]:
            rtt_ms = float(rtt_resp["data"]["result"][0]["value"][1]) * 1000
        if loss_resp["data"]["result"]:
            packet_loss = float(loss_resp["data"]["result"][0]["value"][1])

        if rtt_ms is not None and packet_loss is not None:
            print(f"Inserindo ping: {target}, {rtt_ms}, {packet_loss}")
            cursor.execute(
                "INSERT INTO ping_results (host, rtt_ms, packet_loss) VALUES (%s, %s, %s)",
                (target, rtt_ms, packet_loss)
            )

    conn.commit()


def save_http_results(conn):
    cursor = conn.cursor()
    for target in targets:
        status_query = f'probe_http_status_code{{target="{target}"}}'
        time_query = f'probe_http_duration_seconds{{target="{target}"}}'

        status_resp = query_prometheus(status_query)
        time_resp = query_prometheus(time_query)

        status_code = None
        response_time_ms = None

        if status_resp["data"]["result"]:
            status_code = int(status_resp["data"]["result"][0]["value"][1])
        if time_resp["data"]["result"]:
            response_time_ms = float(time_resp["data"]["result"][0]["value"][1]) * 1000

        if status_code is not None and response_time_ms is not None:
            print(f"Inserindo HTTP: {target}, {status_code}, {response_time_ms}")
            cursor.execute(
                "INSERT INTO http_results (host, status_code, load_time_ms) VALUES (%s, %s, %s)",
                (target, status_code, response_time_ms)
            )

    conn.commit()


@app.get("/scrape")
def scrape_and_save():
    print("Coletando métricas")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    try:
        save_ping_results(conn)
        save_http_results(conn)
    finally:
        conn.close()
    print("Coleta e salvamento concluídos")
    return {"status": "ok"}
