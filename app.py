import os
import requests
from flask import Flask, request, jsonify
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION", "us-east-1")

s3 = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data = request.json
    voice_id = data.get("voice_id", "Bella")
    model_id = data.get("model_id", "eleven_monolingual_v1")
    script = data.get("text")
    stability = data.get("stability", 0.75)
    similarity_boost = data.get("similarity_boost", 0.75)

    if not script:
        return jsonify({"error": "Missing 'text' in request"}), 400

    eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Accept": "audio/mpeg",
        "Content-Type": "application/json"
    }
    payload = {
        "text": script,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost
        }
    }

    response = requests.post(eleven_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        return jsonify({"error": "Failed to synthesize audio", "details": response.text}), 500

    filename = f"celsius_ad_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.mp3"
    s3.upload_fileobj(
        response.raw,
        S3_BUCKET,
        filename,
        ExtraArgs={'ContentType': 'audio/mpeg', 'ACL': 'public-read'}
    )

    public_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
    return jsonify({"audio_url": public_url})

if __name__ == "__main__":
    app.run(debug=True)
