from flask import Flask, request
from jsonrpcserver import method, Result, Success, Error, dispatch
from ocr import exec_ocr, exec_capture, exec_translate

app = Flask(__name__)
image_cache = {}

@method
def add(a: int, b: int) -> Result:
    global image_cache  # グローバル変数を参照することを明示
    print("add request")
    print(exec_ocr(image_cache))
    return Success(a + b)

@method
def ocr() -> Result:
    global image_cache  # グローバル変数を参照することを明示
    print("ocr request")
    ocr_result = exec_ocr(image_cache)
    print(ocr_result)
    translate_result = exec_translate(ocr_result)
    print(translate_result)
    return Success(translate_result)

@method
def capture() -> Result:
    global image_cache  # グローバル変数を参照することを明示
    print("capture request")
    image_cache = exec_capture()
    return Success()

@app.route("/api", methods=["POST"])
def api():
    data = request.get_data(as_text=True)
    print("Raw request data:", data)
    # validate_result=False で検証を無効にする（バージョンによっては利用可能なオプションです）
    response = dispatch(data)
    if isinstance(response, str):
        return response, 200, {"Content-Type": "application/json"}
    else:
        return response.serialize(), 200, {"Content-Type": "application/json"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=25049)
