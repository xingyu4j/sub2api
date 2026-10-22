# GitHub 配置说明

本目录的 CI 和发布流程用于 `xingyu4j/sub2api`。Release 和 GHCR 的目标地址根据当前仓库自动生成，默认不需要配置额外 Secret。

## 工作流

| 文件 | 触发方式 | 用途 |
| --- | --- | --- |
| `workflows/backend-ci.yml` | 推送代码、Pull Request | 部署脚本检查、Go 单元及集成测试、前端 lint/类型检查/关键测试、发布工具回归测试 |
| `workflows/security-scan.yml` | 推送代码、Pull Request、每周一 03:00 UTC、手动 | Go 漏洞扫描、前端生产依赖漏洞审计 |
| `workflows/release.yml` | 推送 `v*` 标签、手动 | 构建前端和多平台二进制，发布 Release 和 GHCR 镜像 |
| `workflows/cla.yml` | PR、Issue 评论 | 仅在上游仓库运行；本仓库跳过，因为现有 CLA 指定的是上游项目所有者 |

`audit-exceptions.yml` 保存有期限的漏洞例外，目前只保留 `xlsx` 导出场景的两项已有例外。扫描遇到网络错误或无效结果会失败；新增高危漏洞不会被自动忽略。

`SECURITY.md` 指向本仓库的私密漏洞报告入口。`release-tools/` 中的脚本生成构建矩阵、校验产物来源、发布镜像并同步版本号，其依赖固定在 `requirements-release.txt`。

## 仓库设置

1. 在 **Actions** 页面启用工作流，并允许工作流引用的 Actions。
2. Release 使用 GitHub 自动提供的 `GITHUB_TOKEN`。工作流已声明发布所需的 `contents: write` 和 `packages: write`，仓库或组织策略需要允许这两项权限。
3. 首次发布后，将 `ghcr.io/xingyu4j/sub2api` 对应的 Package 设置为 **Public**，供服务器匿名拉取镜像。
4. 在仓库安全设置中启用 **Private vulnerability reporting**，供 `SECURITY.md` 中的链接使用。
5. 如果默认分支保护规则禁止 Actions 直接提交版本号，将仓库变量 `SYNC_VERSION_FILE` 设为 `false`，并自行维护 `backend/cmd/server/VERSION`。

## 可选变量与密钥

| 类型 | 名称 | 用途 |
| --- | --- | --- |
| Variable | `SIMPLE_RELEASE` | 标签触发时设为 `true` 则仅发布 Linux amd64 GHCR 镜像；脚本安装和在线更新需要保持未设置或 `false` |
| Variable | `SYNC_VERSION_FILE` | 设为 `false` 可关闭完整正式版发布后的版本号同步 |
| Secret | `DOCKERHUB_USERNAME`、`DOCKERHUB_TOKEN` | 同时配置后，完整发布额外推送 Docker Hub；缺少任意一项时跳过 |
| Secret | `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID` | 同时配置后启用现有发布通知；未配置时跳过 |

## 首次发布

先推送包含本次修改的 `main`，再创建指向该提交的新版本标签。版本号应高于服务器当前版本；下面的 `X.Y.Z` 需要替换为实际数字。

```bash
git push origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

只推送本次新建的标签。`git push --tags` 会同时推送克隆时保留的上游历史标签，并触发对应的发布任务。

在 Actions 中手动运行 Release 时，`tag` 填写已经存在的版本标签，`simple_release` 和 `dry_run` 均选择 `false`。手动选择优先于仓库的 `SIMPLE_RELEASE` 变量。

完整发布成功后，确认 Release 包含 Linux amd64、arm64 压缩包和 `checksums.txt`，再按 [服务器迁移说明](../deploy/README.md#switching-an-existing-server)切换现有服务器。

推送 `main` 会执行 CI；安装包和镜像由标签发布流程生成。GitHub 上的实际运行结果还取决于仓库权限、分支规则及托管 Runner，首次发布前可以使用 [dry run](release-tools/README.md#validate-without-publication)验证完整构建。
