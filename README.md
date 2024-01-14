# srctag-action

Tell about the impacts of your PullRequests. By networking your source files and issues.

## Example

<img width="468" alt="image" src="https://github.com/williamfzc/srctag/assets/13421694/a63c52c7-f2db-4742-8728-2b82c989b5d1">

https://github.com/williamfzc/srctag/pull/4#issuecomment-1890517102

## Installation

### 1. Install GitHub App

https://github.com/apps/srctag

### 2. Add GitHub Action

```yaml
name: srctag
on:
  pull_request:
    branches:
      - '*'

jobs:
  srctag_test:
    runs-on: ubuntu-latest
    name: srctag test
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: srctag
        uses: williamfzc/srctag-action@main
```

### 3. Run and check the comment

## License

[Apache2.0](LICENSE)
