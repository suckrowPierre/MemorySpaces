import audio_interface_helper as aih

def main():
    print(aih.get_devices_names(aih.get_out_devices()))


if __name__ == '__main__':
    main()