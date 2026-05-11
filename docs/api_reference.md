# 问年 WenNian API Reference v2.0.0

## Base URL
`http://localhost:8000`

## Endpoints

### Health Check
```
GET /api/v1/health
```
Response: `{"status": "ok", "version": "2.0.0"}`

### Aging Assessment
```
POST /api/v1/evaluate
Content-Type: application/json
```
Request body:
```json
{
  "biomarkers": {
    "age": 40.0,
    "albumin": 43.0,
    "creatinine": 75.0,
    "glucose": 5.1,
    "c_reactive_protein": 1.0,
    "lymphocyte_percent": 33.0,
    "mcv": 90.0,
    "rdw": 13.0,
    "alkaline_phosphatase": 70.0,
    "white_blood_cell_count": 6.5
  }
}
```
Response: Biological age, confidence intervals, per-clock results, audit output.

## Error Codes
- 400: Missing biomarkers
- 422: Validation failure (invalid biomarker values)
- 500: Server error

## Disclaimer
本API不构成医疗诊断。所有结果仅供健康参考。
