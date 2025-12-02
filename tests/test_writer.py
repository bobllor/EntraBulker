from backend.core.azure_writer import AzureWriter
from pathlib import Path
from backend.support.vars import DEFAULT_OPCO_MAP
from backend.support.types import Response
import backend.support.utils as utils

names: list[str] = ["John Doe", "Jane Doe", "Krane Doe"]
usernames: list[str] = utils.generate_usernames(names, ["" for _ in range(len(names))], DEFAULT_OPCO_MAP)
passwords: list[str] = [utils.generate_password(20) for _ in range(len(names))]

text: str = "Hello [USERNAME] I am [NAME] and your password is [PASSWORD]"

def test_write_text(tmp_path: Path):
    writer: AzureWriter = AzureWriter(project_root=tmp_path)

    writer.set_full_names(names)
    writer.set_usernames(usernames)
    writer.set_passwords(passwords)

    res: Response = writer.write_template(tmp_path, text=text)

    if res["status"] == "error":
        raise AssertionError(f"Failed to validate CSV")
    
    output_dir: Path = Path(res["output_dir"])

    for file in output_dir.iterdir():
        with open(file, "r") as file:
            content: str = file.read()

        write_status: bool = False

        # checking the contents of the output dir.
        for i, name in enumerate(names):
            username: str = usernames[i]
            password: str = passwords[i]

            if username in content and password in content \
                and name in content:
                write_status = True
        
        if not write_status:
            raise AssertionError(f"Failed to write to file for {file.name}: {content}")

def test_fail_write_csv_no_names(tmp_path: Path):
    writer: AzureWriter = AzureWriter(project_root=tmp_path)

    writer.set_full_names(names)
    writer.set_passwords(passwords)

    res: Response = writer.write_template(tmp_path, text=text)

    assert res["status"] == "error"

def test_fail_write_csv_no_usernames(tmp_path: Path):
    writer: AzureWriter = AzureWriter(project_root=tmp_path)

    writer.set_usernames(usernames)
    writer.set_passwords(passwords)

    res: Response = writer.write_template(tmp_path, text=text)

    assert res["status"] == "error"

def test_fail_write_csv_no_passwords(tmp_path: Path):
    writer: AzureWriter = AzureWriter(project_root=tmp_path)

    writer.set_full_names(names)
    writer.set_usernames(usernames)

    res: Response = writer.write_template(tmp_path, text=text)

    assert res["status"] == "error"