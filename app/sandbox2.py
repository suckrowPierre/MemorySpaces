import audio_interface_helper


def main():
    outdevices = audio_interface_helper.get_out_devices()
    print(outdevices)

if __name__ == "__main__":
    main()
