import os
import base64
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)

# Reads ANTHROPIC_API_KEY from environment — set it before running:
#   export ANTHROPIC_API_KEY="sk-ant-..."
client = anthropic.Anthropic()


@app.route('/')
def index():
    with open('index.html', 'r') as f:
        return render_template_string(f.read())


@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']

    try:
        image_data = file.read()
        b64_img = base64.b64encode(image_data).decode('utf-8')

        media_type = file.mimetype
        if media_type not in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
            media_type = 'image/png'

        prompt = """You are an expert chemist. Analyze this Lewis structure diagram of a chemical molecule.

Carefully examine:
- All atoms shown (C, H, N, O, S, P, halogens, etc.) — note that carbon atoms at line intersections or endpoints are often unlabeled
- All bonds: single line = single bond, double parallel lines = double bond, triple parallel lines = triple bond
- Wedge/dash bonds indicating 3D stereochemistry if present
- Implicit hydrogens on carbon (carbons with fewer than 4 explicit bonds have implicit H to fill valence)
- Any formal charges (+ or −) shown on atoms
- Ring structures (benzene rings, cyclic structures)

Return ONLY the canonical SMILES string. No explanation, no markdown, no extra text — just the SMILES."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": b64_img,
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        smiles_string = response.content[0].text.strip()
        return jsonify({'smiles': smiles_string})

    except anthropic.AuthenticationError:
        return jsonify({'error': 'Invalid or missing ANTHROPIC_API_KEY. Set it with: export ANTHROPIC_API_KEY="sk-ant-..."'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8080)
