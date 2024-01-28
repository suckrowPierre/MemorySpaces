import audioldm2


def main():
    model_path = "../data/models/audioldm2"
    device = "cuda"
    pipe = audioldm2.setup_pipeline(model_path, device)
    parameters = audioldm2.generate_params("hello world")
    audio = audioldm2.text2audio(pipe, parameters)
    
    if(audio is not None):
        print("audio is not None")

if __name__ == '__main__':
    main()