# Run CommitShield VFD

- Obtain a [GitHub API authentication token](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api?apiVersion=2022-11-28)

- Create a `.env` file at the root of the project and insert the following variables into it:
  - `GITHUB_TOKEN`: your GitHub API authentication token
  - Depending on the LLM(s) used:
    - `LOCALHOST_URL`: the URL to access your local LLM
    - `OPENAI_API_KEY`: your OpenAI API key
    - `MISTRAL_API_KEY`: your MistralAI API key

- Build the image of the project from the Dockerfile:

```
docker build -t commitshield .
```

- Create and run the container:

```
docker run --name commitshield -it commitshield bash
```

- Once in the container, go to the `VFD` folder:

```bash
cd VFD
```

- _Mandatory_: Set the value of the `checkpoint.txt` file to 0 to analyze commits from the first one in the list

- To launch the vulnerability fix detection, either:
  - run a shell script:

  ```bash
  bash <shell_script>
  ```

  - create a `path.txt` file (if it doesn't exist), insert commits into it and run the Python program:

  ```bash
  python vul_fix_check.py --llm <llm>
  ```
