# Major Feats

- <b>NCM 2.0 and Nutanix Central (NC) Integration: </b> Now you can connect DSL client with Nutanix Central (NC) instance and use NCM 2.0 where NCM application runs on the Nutanix Central on-premises and uses the same Kubernetes-based Service Microservices Platform (SMSP). This release supports following deployment models:
  - **Opt-out (on-prem)**: Direct connection with Prism Central/Self Service Vm using `calm init dsl`

  ```
    Prism/Nutanix Central Host []: 10.44.76.74
    Port [9440]: 
    Username [admin]: 
    Password []: 
    Project [-]: auto_ncm_default
    [2026-03-09 06:03:16] [INFO] [calm.dsl.cli.init_command:339] Checking if Calm is enabled on Server
    [2026-03-09 06:03:17] [INFO] [calm.dsl.cli.init_command:349] ENABLED
    [2026-03-09 06:03:19] [INFO] [calm.dsl.cli.init_command:370] Policy enabled=True
    [2026-03-09 06:03:19] [INFO] [calm.dsl.cli.init_command:389] Approval Policy enabled=True
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:408] stratos enabled=True
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:415] CP enabled=True
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:421] Verifying the project details
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:428] Project 'auto_ncm_default' verified successfully
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:463] Updating context for using latest config file data
    [2026-03-09 06:03:20] [INFO] [calm.dsl.cli.init_command:481] Creating local database
    [2026-03-09 06:03:20] [INFO] [calm.dsl.store.cache:224] Updating cache 
    ............................ [Done]

    HINT: To get started, follow the 3 steps below:
    1. Initialize an example blueprint DSL: calm init bp
    2. Add vm image details according to your use in generated HelloBlueprint/blueprint.py
    3. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py
    4. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i

    Keep Calm and DSL On!
  ```

  - **Opt-in NCM 2.0 (via NC details)**: Direct connection to NC by providing NC details during `calm init dsl`. As NC doesn't require any port to connect, default port/any custom port provided will be ignored.

  ```
    (venv) [prabhat.dwivedi@prabhat-dwivedi calm-dsl]$ calm init dsl
    [2026-03-09 05:55:33] [INFO] [calm.dsl.cli.init_command:281] Skip port for Nutanix Central, if provided it will be ignored
    Please provide Calm DSL settings:

    Prism/Nutanix Central Host []: nconprem-10-115-150-8.ccpnx.com
    Port [9440]: 
    Username [admin]: 
    Password []: 
    Project [-]: 
    [2026-03-09 05:55:38] [INFO] [calm.dsl.api.util:1204] NCM is enabled
    [2026-03-09 05:55:39] [INFO] [calm.dsl.builtins.models.helper.common:567] Home PC UUID: 1f1219f2-6f3b-4c18-8ba1-4ec1e718aad4
    [2026-03-09 05:55:39] [INFO] [calm.dsl.cli.init_command:370] Policy enabled=True
    [2026-03-09 05:55:39] [INFO] [calm.dsl.cli.init_command:389] Approval Policy enabled=True
    [2026-03-09 05:55:40] [INFO] [calm.dsl.cli.init_command:408] stratos enabled=True
    [2026-03-09 05:55:40] [INFO] [calm.dsl.cli.init_command:415] CP enabled=True
    [2026-03-09 05:55:40] [INFO] [calm.dsl.cli.init_command:463] Updating context for using latest config file data
    [2026-03-09 05:55:40] [INFO] [calm.dsl.cli.init_command:481] Creating local database
    [2026-03-09 05:55:40] [INFO] [calm.dsl.store.cache:224] Updating cache 
    ............................ [Done]

    HINT: To get started, follow the 3 steps below:
    1. Initialize an example blueprint DSL: calm init bp
    2. Add vm image details according to your use in generated HelloBlueprint/blueprint.py
    3. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py
    4. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i

    Keep Calm and DSL On!
  ```

  - **Opt-in NCM 2.0 (via PC details)**: Automatic detection of NC deployment when providing PC details - fetches NC details if deployed and sets up NCM 2.0 via NC, falls back to opt-out if NC is not deployed. <i>Note: In this scenario: if a PC is deployed with NC-NCM then DSL client cannot be used to handle PC entities like PC projects and users, it will handle NC-NCM entities.</i>

  ```
    (venv) [prabhat.dwivedi@prabhat-dwivedi calm-dsl]$ calm init dsl
    [2026-03-09 05:58:41] [INFO] [calm.dsl.cli.init_command:281] Skip port for Nutanix Central, if provided it will be ignored
    Please provide Calm DSL settings:

    Prism/Nutanix Central Host []: 10.115.150.8
    Port [9440]: 
    Username [admin]: 
    Password []: 
    Project [-]: default
    [2026-03-09 05:59:07] [INFO] [calm.dsl.api.util:1204] NCM is enabled
    [2026-03-09 05:59:07] [INFO] [calm.dsl.builtins.models.helper.common:567] Home PC UUID: 1f1219f2-6f3b-4c18-8ba1-4ec1e718aad4
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:370] Policy enabled=True
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:389] Approval Policy enabled=True
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:408] stratos enabled=True
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:415] CP enabled=True
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:421] Verifying the project details
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:428] Project 'default' verified successfully
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:463] Updating context for using latest config file data
    [2026-03-09 05:59:08] [INFO] [calm.dsl.cli.init_command:481] Creating local database
    [2026-03-09 05:59:09] [INFO] [calm.dsl.store.cache:224] Updating cache 
    ............................ [Done]

    HINT: To get started, follow the 3 steps below:
    1. Initialize an example blueprint DSL: calm init bp
    2. Add vm image details according to your use in generated HelloBlueprint/blueprint.py
    3. Create and validate the blueprint: calm create bp --file HelloBlueprint/blueprint.py
    4. Start an application using the blueprint: calm launch bp Hello --app_name HelloApp01 -i

    Keep Calm and DSL On!
  ```
  

  Key enhancements include:
  - Supported flags for `calm init dsl` can also take NC inputs. Use `calm init dsl --help` to see more information.
  - Supported flags for `calm set config` can also take NC inputs. Use `calm set config --help` to see more information.
  - Store domain registered information in DSL cache for NC. Use command `calm update cache -e domain` or `calm show cache -e domain`

# Improvements

- <b>Added domain attribute to AHV account model for NCM 2.0: </b> AHV account creation now needs registered domain in NC as input to domain attribute. Check example [here](https://github.com/nutanix/calm-dsl/blob/master/examples/accounts/remote_ahv_account_with_domain_attribute.py)
- <b>Enhanced Account Operations: </b> For NCM 2.0 Account verify and delete operations now include polling mechanisms to ensure accounts are properly onboarded/offboarded before completing the operation. This provides better reliability and user feedback during account lifecycle management.

# Bug Fixes

- Fixed security vulnerabilities identified by upgrading dependencies:
  - Jinja2: 3.0.3 → 3.1.6
  - requests: 2.27.0 → 2.32.4
  - requests-toolbelt: 0.9.1 → 1.0.0
  - urllib3: 1.26.20 → 2.6.3
  - libcrypto3: 3.3.3-r0 → 3.5.5-r0
  - libssl3: 3.3.3-r0 → 3.5.5-r0
  - busybox: 1.36.1-r29 → 1.37.0-r30
  - busybox-binsh: 1.36.1-r29 → 1.37.0-r30
  - ssl_client: 1.36.1-r29 → 1.37.0-r30
  - musl-utils: 1.2.5-r0 → 1.2.5-r21
