from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import bi_service
from .analyzer import analyze_and_save
from .data_fetcher import fetch_and_save
from .paths import ROOT_DIR, ensure_data_dir
from .report import generate_report
from .storage import load_bis, load_config, load_json, load_klines, save_config, undo_bis


STATIC_DIR = ROOT_DIR / "chanlun_v2_static"

app = FastAPI(title="中证1000缠论分析系统 v2")
app.mount("/chanlun-v2-static", StaticFiles(directory=STATIC_DIR), name="chanlun-v2-static")


class PenCreate(BaseModel):
    start_dt: str
    end_dt: str
    start_price: float
    end_price: float
    note: str = ""


class PenUpdate(BaseModel):
    note: Optional[str] = ""


class ConfigUpdate(BaseModel):
    obsidian_vault: str = ""


@app.on_event("startup")
def startup() -> None:
    ensure_data_dir()


@app.get("/chanlun-v2")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/v2/fetch")
def fetch() -> dict:
    try:
        return fetch_and_save()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"拉取新浪K线失败：{exc}") from exc


@app.get("/api/v2/state")
def state() -> dict:
    analysis = analyze_and_save()
    return {
        "klines": [item.to_dict() for item in load_klines()],
        "pens": [item.to_dict() for item in load_bis()],
        "segments": analysis["segments"],
        "zhongshu": analysis["zhongshu"],
        "signals": analysis["signals"],
        "summary": analysis["summary"],
        "config": load_config(),
    }


@app.post("/api/v2/pens")
def create_pen(payload: PenCreate) -> dict:
    try:
        return bi_service.create_bi(
            payload.start_dt,
            payload.end_dt,
            payload.start_price,
            payload.end_price,
            payload.note,
        ).to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/v2/pens/{index}")
def update_pen(index: int, payload: PenUpdate) -> dict:
    try:
        return bi_service.update_bi(index, payload.note or "").to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/v2/pens/{index}")
def delete_pen(index: int) -> dict:
    try:
        bi_service.delete_bi(index)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": True}


@app.post("/api/v2/undo")
def undo() -> dict:
    return undo_bis()


@app.post("/api/v2/analyze")
def analyze() -> dict:
    return analyze_and_save()


@app.post("/api/v2/report")
def report() -> dict:
    try:
        return generate_report()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"生成报告失败：{exc}") from exc


@app.post("/api/v2/config")
def config(payload: ConfigUpdate) -> dict:
    return save_config({"obsidian_vault": payload.obsidian_vault})

