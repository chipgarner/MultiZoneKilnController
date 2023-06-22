import FilesHandler

def test_start_firing():
    files = FilesHandler.FilesHandler()
    files.start_firing()

    assert files.create_firing_file_name() == files.firing_name # Can fail once very near the hour

def test_get_firing_file_name():
    files = FilesHandler.FilesHandler()

    name = files.create_firing_file_name()

    assert isinstance(name, str)
    assert len(name)  == 18
    assert name[0:2] == '20'
    assert name[13:18] == '.fire'
