; Script Inno Setup tao trinh cai dat ung dung Quan Ly In An
; Tac gia: Pham Cong Vinh - Truong THPT Bac Dong Quan

#define MyAppName "Quản lý in ấn"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Phạm Công Vinh - Trường THPT Bắc Đông Quan"
#define MyAppExeName "QuanLyInAn.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".myp"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Thong tin dinh danh duy nhat cho ung dung (Khong thay doi GUID nay giua cac lan cap nhat)
AppId={{E79C9D18-682E-4C2E-80A7-681FB7239C93}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://thptbacdongquan.edu.vn
AppSupportURL=https://thptbacdongquan.edu.vn
AppUpdatesURL=https://thptbacdongquan.edu.vn
DefaultDirName={autopf}\QuanLyInAn
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Duong dan luu file cai dat dau ra
OutputDir=release
OutputBaseFilename=QuanLyInAn_Setup_v1.0.0
SetupIconFile=app\resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
; Nen du lieu toi da giup file cai dat cuc nhe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.CreateDesktopIcon=Tạo biểu tượng trên màn hình nền (Desktop)
english.AdditionalIcons=Biểu tượng bổ sung:
english.LaunchProgram=Khởi chạy %1 ngay bây giờ

[Messages]
WelcomeLabel1=Chào mừng bạn đến với trình cài đặt %1
WelcomeLabel2=Trình cài đặt sẽ hướng dẫn bạn cài đặt phần mềm Quản lý in ấn đề thi & tài liệu lên máy tính.%n%n• Tác giả: Phạm Công Vinh%n• Chức vụ: Bí thư chi đoàn 11A5, Chủ tịch CLB Nghiên cứu Khoa học, STEM và Robotics%n• Đơn vị: Trường THPT Bắc Đông Quan%n%nKhuyến nghị bạn đóng tất cả các ứng dụng khác trước khi tiếp tục.
SelectDirBrowseLabel=Để tiếp tục, hãy nhấn 'Next'. Nếu bạn muốn chọn một thư mục khác, hãy nhấn 'Browse'.
FinishedHeadingLabel=Hoàn tất cài đặt %1
FinishedLabel=Ứng dụng %1 đã được cài đặt thành công vào máy tính của bạn.%n%nNhấn 'Finish' để đóng trình cài đặt.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copy toan bo file build onedir tu dist\QuanLyInAn vao thu muc cai dat
Source: "dist\QuanLyInAn\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Cap quyen ghi day du cho thu muc du lieu va backups tranh loi phan quyen Windows
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\DeDaIn"; Permissions: users-modify
Name: "{app}\backups"; Permissions: users-modify

[Icons]
; Shortcut trong Start Menu
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"
; Shortcut ngoai Desktop
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Tuy chon mo app ngay sau khi cai dat xong
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
