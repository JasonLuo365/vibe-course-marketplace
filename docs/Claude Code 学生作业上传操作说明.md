# Claude Code 学生作业上传操作说明

适用于使用 Claude Code 完成 Vibe Coding 课程作业的学生。请按本说明操作；无需安装 Docker，也无需填写提交服务器地址。

## 你需要准备

- 已安装并能够在本机终端运行 Claude Code；
- 网络连接；
- 教师提供的课程邀请码和作业编号；
- 一个保存作业代码的本地文件夹。

## 第一次使用：安装与注册

1. 打开 PowerShell，粘贴并执行课程提供的安装命令：

   ```powershell
   irm https://raw.githubusercontent.com/JasonLuo365/vibe-course-marketplace/v0.1.8/scripts/install-claude-submit.ps1 | iex
   ```

   这一步会安装提交工具，并为 Claude Code 添加 `/submit-homework` 命令。服务地址会自动配置，学生不需要输入网址。

2. 关闭 PowerShell 和 Claude Code，然后重新打开 PowerShell，执行：

   ```powershell
   vibe-submit setup
   ```

3. 按提示依次输入课程邀请码、学号、姓名和密码。密码仅在本机终端输入，不要发送到 Claude 对话里。

看到注册成功提示后，本台电脑通常不需要再次注册。

## 每次提交作业

1. 在 PowerShell 进入**作业代码所在的文件夹**：

   ```powershell
   cd <你的作业文件夹>
   ```

   例如代码在“桌面\\作业一”文件夹中，就应先进入该文件夹。不要在桌面、下载目录或其他课程项目的文件夹里启动 Claude Code。

2. 在该文件夹启动 Claude Code：

   ```powershell
   claude
   ```

3. 在当前 Claude Code 对话中输入：

   ```text
   /submit-homework <作业编号>
   ```

   将 `<作业编号>` 替换为教师给出的编号。例如：`/submit-homework homework-01`。

4. Claude 会先生成预览，显示将要提交的文件、当前会话和文件大小。请重点确认：

   - 当前目录是本次作业目录；
   - 文件列表中包含你的代码；
   - 会话确实是当前作业的 Claude 对话；
   - 没有不希望提交的文件。

   当前 Claude Code 会话内容会随作业一起提交，用于教师了解你的完成过程。

5. 预览无误后，在 Claude 的确认问题中明确回复“确认提交”。只有明确确认后才会上传；取消或不确认不会上传任何内容。

6. 看到“提交成功”后即完成。请保留终端输出或截图作为提交凭证。

## 重新提交

请先在正确的作业文件夹重新启动 Claude Code，然后再次执行同一条 `/submit-homework <作业编号>` 命令。

系统默认保护已有提交。若确实需要用新版本替换旧版本，请在 Claude 询问时明确说明“确认覆盖原提交”；不要在不确定时要求覆盖。

## 常见问题

### 找不到 `/submit-homework`

先彻底关闭再重新打开 Claude Code。仍然找不到时，重新执行一次安装命令，然后重新打开终端和 Claude Code。

### 提交的文件不对或教师端看不到最新代码

通常是 Claude Code 启动目录不正确。退出 Claude Code，先用 `cd` 进入包含代码的作业文件夹，再运行 `claude` 并重新提交。

### 上传失败或网络中断

提交包会保存在本机等待重试。网络恢复后，在 PowerShell 运行：

```powershell
vibe-submit retry
```

### 注册或密码问题

不要将密码发送给 Claude。请联系课程教师或助教处理账号信息。
