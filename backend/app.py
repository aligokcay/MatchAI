from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import joblib

# Flask uygulamasını başlat
app = Flask(__name__)
CORS(app)  # CORS sorunlarını önlemek için

# 1️⃣ MODELLERİ VE DÖNÜŞTÜRÜCÜLERİ YÜKLE
load_model = tf.keras.models.load_model
result_model = load_model("result_model.h5", compile=False)
goals_model = load_model("goals_model.h5", compile=False)
scaler = joblib.load("scaler.pkl")
encoder = joblib.load("encoder.pkl")

# Kullanılabilir formasyonlar
formations = ["3-4-1-2", "4-2-3-1", "4-3-3", "4-4-2", "4-1-4-1", "3-4-3"]

# 2️⃣ API Ana Sayfası
@app.route('/')
def home():
    return "Skor Tahmin API Çalışıyor!"

# 3️⃣ Tahmin Yapma Endpoint'i
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Kullanıcıdan gelen JSON verisini al
        data = request.json  
        
        # Gerekli özellikleri al
        opponent_market_value = data["opponent_market_value"]
        competition = data["competition"]
        home_away = data["home_away"]
        formation = data["formation"]
        opponent_formation = data["opponent_formation"]

        # Veriyi encode et ve ölçekle
        new_match_encoded = np.hstack((
            scaler.transform(np.array([[opponent_market_value]])),
            encoder.transform([[competition, home_away, formation, opponent_formation]]).toarray()
        ))

        # Model tahmini yap
        result_prediction = result_model.predict(new_match_encoded)
        goals_prediction = goals_model.predict(new_match_encoded)

        # Sonucu belirle
        result_categories = ['W', 'D', 'L']
        predicted_result_idx = np.argmax(result_prediction)
        predicted_result = result_categories[predicted_result_idx]
        predicted_goals = goals_prediction[0].tolist()

        # Yanıtı döndür
        return jsonify({
            "predicted_result": predicted_result,
            "predicted_goals": {
                "goals_for": round(predicted_goals[0], 1),
                "goals_for_opponent": round(predicted_goals[1], 1)
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    

# En İyi Formasyon Endpoint'i
@app.route('/recommend-formation', methods=['POST'])
def best_formation():
    try:
        print('Best Form')
        data = request.json  
        opponent_market_value = data["opponent_market_value"]
        competition = data["competition"]
        home_away = data["home_away"]
        opponent_formation = data["opponent_formation"]

        best_formation = None
        best_goal_difference = float('-inf')

        for formation in formations:
            new_match_encoded = np.hstack((
                scaler.transform(np.array([[opponent_market_value]])),
                encoder.transform([[competition, home_away, formation, opponent_formation]]).toarray()
            ))
            goals_prediction = goals_model.predict(new_match_encoded)
            atilan_gol, yenilen_gol = goals_prediction[0]
            goal_difference = float(atilan_gol - yenilen_gol)
            
            if goal_difference > best_goal_difference:
                best_goal_difference = goal_difference
                best_formation = formation

        return jsonify({
            "best_formation": best_formation,
            "goal_difference": round(best_goal_difference, 1)
        })

    except Exception as e:
        import traceback
        print("Hata:", traceback.format_exc())  # Tüm hata detaylarını göster
        return jsonify({"error": str(e)}), 400

# 4️⃣ Flask Sunucusunu Çalıştır
if __name__ == '__main__':
    app.run(debug=True)
