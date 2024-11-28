from ostilhou.asr.models import load_model, get_all_models



def test_show_models():
    print(get_all_models())

def test_load_model():
    model = load_model("vosk-br-0.7")