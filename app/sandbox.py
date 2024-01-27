import settings

def main():
    settings_cache = settings.SettingsCache()
    print(settings_cache.get_settings_replaced_drop_down())
    


if __name__ == '__main__':
    main()