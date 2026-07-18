# 해외채권 리스크 진단 대시보드

"채권은 왜 안 걷히는가"를 여신한도·부보·연령·DSO 네 가지 각도에서 진단하는 인터랙티브 Plotly + Streamlit 대시보드.

- 데이터: 학습용 합성 데이터 (해외법인 채권잔액·여신한도/부보·대손충당금·팩토링·회수·매출 6종)
- 차트 6종: 부보여부별 연체비중(matplotlib vs Plotly 비교) · 법인별 활용률×연체비중 · 연령구간별 대손충당금비율 · 법인별 연체율 · 부보기관별 연체율 · DSO×활용률 산점도

## 로컬 실행

```
pip install -r requirements.txt
streamlit run app.py
```

## 폴더 구조

```
data/          원본 CSV 6종
charts/        차트 생성 스크립트 (data_prep.py 공용 전처리 모듈 포함)
charts/output/ matplotlib 이미지 출력 (gitignore)
app.py         Streamlit 앱
```
