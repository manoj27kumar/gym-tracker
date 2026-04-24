import streamlit as st
import sqlite3
import pandas as pd

import os
st.write(os.getcwd())

# Connect database
conn = sqlite3.connect("gym.db", check_same_thread=False)
c = conn.cursor()

# Create table
c.execute('''
CREATE TABLE IF NOT EXISTS workouts (
    date TEXT,
    exercise TEXT,
    sets INTEGER,
    reps INTEGER,
    weight REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS diet (
    date TEXT,
    protein REAL,
    calories REAL
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS bodyweight (
    date TEXT,
    weight REAL
)
''')
conn.commit()

# UI

st.set_page_config(
    page_title="Gym Tracker",
    page_icon="💪",
    layout="wide"
)

st.markdown("""
    <style>
    .main {
        background-color: #f5f7fa;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

import datetime

date = st.date_input("Date", datetime.date.today())

st.title("💪 Gym Tracker")

exercise = st.text_input("Exercise",key="workout_exercise_edit")
sets = st.number_input("Sets", min_value=1, key="workout_sets_edit")
reps = st.number_input("Reps", min_value=1, key="workout_reps_edit")
weight = st.number_input("Weight (kg)", min_value=0, key="workout_weight_edit")

# Save button
if st.button("Save Workout"):
  c.execute(
    "INSERT INTO workouts (date, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?)",
    (str(date), exercise, sets, reps, weight)
  )
  conn.commit()
st.success("Workout Saved!")

# side bar navigation
st.sidebar.title("💪 Gym Tracker")

menu = st.sidebar.radio(
    "Navigation",
    ["Workout", "Diet", "Body Weight", "Analytics"]
)

# workout session with date
import datetime

if menu == "Workout":
    st.title("💪 Workout Tracker")

    col1, col2 = st.columns(2)

    with col1:
        exercise = st.text_input("🏋️ Exercise", key="workout_exercise")
        sets = st.number_input("🔁 Sets", min_value=1, key="workout_sets")

    with col2:
        reps = st.number_input("🎯 Reps", min_value=1, key="workout_reps")
        weight = st.number_input("🏋️ Weight (kg)", min_value=0, key="workout_weight")

    date = st.date_input("📅 Date", key="workout_date")

    if st.button("💾 Save Workout", key="save_workout_btn"):
        c.execute(
            "INSERT INTO workouts (date, exercise, sets, reps, weight) VALUES (?, ?, ?, ?, ?)",
            (str(date), exercise, sets, reps, weight)
        )
        conn.commit()
        st.success("✅ Workout Saved!")

# diet tracker
if menu == "Diet":
    st.title("🍗 Diet Tracker")

    col1, col2 = st.columns(2)

    with col1:
        protein = st.number_input("🥩 Protein (g)", key="diet_protein")

    with col2:
        calories = st.number_input("🔥 Calories", key="diet_calories")

    date = st.date_input("📅 Date", key="diet_date")

    if st.button("💾 Save Diet", key="save_diet_btn"):
        c.execute("INSERT INTO diet VALUES (?, ?, ?)",
                  (str(date), protein, calories))
        conn.commit()
        st.success("✅ Diet Saved!")

# body weight tracker
if menu == "Body Weight":
    st.title("⚖️ Body Weight Tracker")

    weight = st.number_input("⚖️ Weight (kg)", key="bw_weight")
    date = st.date_input("📅 Date", key="bw_date")

    if st.button("💾 Save Weight", key="save_bw_btn"):
        c.execute("INSERT INTO bodyweight VALUES (?, ?)",
                  (str(date), weight))
        conn.commit()
        st.success("✅ Weight Saved!")


#analytics 
import pandas as pd
import plotly.express as px

from sklearn.linear_model import LinearRegression
import numpy as np

if menu == "Analytics":
    st.title("📊 Analytics Dashboard")

    df = pd.read_sql("SELECT * FROM workouts", conn)

    bw_df = pd.read_sql("SELECT * FROM bodyweight", conn)

    if not df.empty:

        df['date'] = pd.to_datetime(df['date'])

        df['week'] = df['date'].dt.isocalendar().week

        weekly = df.groupby('week').agg({
            'weight': 'mean',
            'exercise': 'count'
        }).reset_index()

        import plotly.express as px

        st.subheader("📊 Weekly Average Weight")

        fig_week = px.bar(
            weekly,
            x='week',
            y='weight',
            title="Weekly Avg Weight"
        )

        st.plotly_chart(fig_week, use_container_width=True)

        st.subheader("📅 Weekly Workout Count")

        fig_count = px.line(
            weekly,
            x='week',
            y='exercise',
            title="Workouts per Week"
        )

        st.plotly_chart(fig_count, use_container_width=True)

        if len(weekly) > 1:
            if weekly['weight'].iloc[-1] > weekly['weight'].iloc[-2]:
                st.success("🔥 You are improving week by week!")
        else:
            st.warning("⚠️ Try increasing your weights!")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Workouts", len(df))

        with col2:
            st.metric("Max Weight", df['weight'].max())

        with col3:
            st.metric("Avg Weight", round(df['weight'].mean(), 2))

        st.subheader("📈 Workout Progress")

        fig = px.line(df, x="date", y="weight", color="exercise")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available")

    if not bw_df.empty:
        bw_df['date'] = pd.to_datetime(bw_df['date'])

        # Convert date to number
        bw_df['day'] = (bw_df['date'] - bw_df['date'].min()).dt.days

        X = bw_df[['day']]
        y = bw_df['weight']

        model = LinearRegression()
        model.fit(X, y)

        
        future_days = np.array(range(X['day'].max() + 1, X['day'].max() + 8)).reshape(-1, 1)

        predictions = model.predict(future_days)

        future_dates = pd.date_range(
            start=bw_df['date'].max(),
            periods=7
        )

        pred_df = pd.DataFrame({
            'date': future_dates,
            'predicted_weight': predictions
        })


        import plotly.graph_objects as go

        st.subheader("🔮 Weight Prediction (Next 7 Days)")

        fig = go.Figure()

        # Actual data
        fig.add_trace(go.Scatter(
            x=bw_df['date'],
            y=bw_df['weight'],
            mode='lines+markers',
            name='Actual'
        ))

        # Predicted data
        fig.add_trace(go.Scatter(
            x=pred_df['date'],
            y=pred_df['predicted_weight'],
            mode='lines+markers',
            name='Predicted'
        ))

        st.plotly_chart(fig, use_container_width=True)


        if predictions[-1] > bw_df['weight'].iloc[-1]:
            st.success("🔥 You are on track to gain weight!")
        else:
            st.warning("⚠️ Weight gain is slow, increase calories/protein")
        

# Show data
st.subheader("📊 Workout History")

df = pd.read_sql("SELECT * FROM workouts", conn)
st.dataframe(df)

import matplotlib.pyplot as plt

if not df.empty:
    st.subheader("📈 Weight Progress")

    fig, ax = plt.subplots()
    ax.plot(df['weight'])
    ax.set_xlabel("Workout Number")
    ax.set_ylabel("Weight")

    st.pyplot(fig)