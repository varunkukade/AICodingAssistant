import os


def process_files(file_paths):
    results = []
    for path in file_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                files = os.listdir(path)
                for f in files:
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path):
                        with open(full_path, "r") as file:
                            content = file.read()
                            if "error" in content:
                                results.append({"file": full_path, "status": "error"})
                            else:
                                results.append({"file": full_path, "status": "ok"})
            else:
                with open(path, "r") as file:
                    content = file.read()
                    if "error" in content:
                        results.append({"file": path, "status": "error"})
                    else:
                        results.append({"file": path, "status": "ok"})
        else:
            results.append({"file": path, "status": "missing"})
    return results


def print_summary(results):
    error_count = 0
    ok_count = 0
    missing_count = 0
    for r in results:
        if r["status"] == "error":
            error_count += 1
        elif r["status"] == "ok":
            ok_count += 1
        elif r["status"] == "missing":
            missing_count += 1
    print("Summary:")
    print("OK files:", ok_count)
    print("Files with errors:", error_count)
    print("Missing files:", missing_count)


if __name__ == "__main__":
    file_list = ["logs/app.log", "logs/debug.log", "data/input.txt", "missing.txt"]
    output = process_files(file_list)
    print_summary(output)
