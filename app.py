from flask import Flask, request, jsonify
from flask_cors import CORS
import mercadopago
import os



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

ACCESS_TOKEN = "APP_USR-7801899979492888-053018-d5c1efe4c0b2b4909fbbca1920235fd8-2013746147"
sdk = mercadopago.SDK(ACCESS_TOKEN)

# Lista para armazenar os pagamentos
pagamentos_realizados = []

@app.route("/pix", methods=["POST"])
def gerar_pix():
    data = request.json
    if not data or "valor" not in data:
        return jsonify({"error": "valor não enviado"}), 400

    try:
        valor = float(data.get("valor", 0.01))
    except Exception:
        return jsonify({"error": "valor inválido"}), 400

    # Dados do cliente
    first_name = data.get("first_name", "Cliente")
    last_name = data.get("last_name", "")
    email = data.get("email", "teste@email.com")
    cpf = data.get("cpf", "00000000000")
    texto_extra = data.get("texto_extra", "")

    payment_data = {
        "transaction_amount": valor,
        "description": f"Pagamento teste PIX - {texto_extra}",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "identification": {
                "type": "CPF",
                "number": cpf
            }
        }
    }

    try:
        payment_response = sdk.payment().create(payment_data)
        response = payment_response["response"]

        # Armazena os dados do pagamento
        pagamentos_realizados.append({
            "payment_id": response["id"],
            "nome": f"{first_name} {last_name}",
            "email": email,
            "cpf": cpf,
            "valor": valor,
            "status": "pendente"
        })

        return jsonify({
            "payment_id": response["id"],
            "qr_code": response["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": response["point_of_interaction"]["transaction_data"]["qr_code_base64"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/status/<payment_id>", methods=["GET"])
def verificar_status(payment_id):
    try:
        payment = sdk.payment().get(payment_id)
        status = payment["response"]["status"]

        # Atualiza o status na lista
        for pag in pagamentos_realizados:
            if str(pag["payment_id"]) == str(payment_id):
                pag["status"] = status
                break

        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/pagamentos", methods=["GET"])
def listar_pagamentos_aprovados():
    aprovados = [pag for pag in pagamentos_realizados if pag["status"] == "approved"]
    return jsonify(aprovados)
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)