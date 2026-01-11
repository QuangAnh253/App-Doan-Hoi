; *** Inno Setup version 6.0.0+ Vietnamese messages ***
;
; To download user-contributed translations of this file, go to:
;   https://jrsoftware.org/files/istrans/
;
; Note: When translating this text, do not add periods (.) to the end of
; messages that didn't have them already, because on those messages Inno
; Setup adds the periods automatically (appending a period would result in
; two periods being displayed).

[LangOptions]
LanguageName=Ti<1EBF>ng Vi<1EC7>t
LanguageID=$042A
LanguageCodePage=1258

[Messages]

; *** Application titles
SetupAppTitle=Cài đặt
SetupWindowTitle=Cài đặt - %1
UninstallAppTitle=Gỡ cài đặt
UninstallAppFullTitle=Gỡ cài đặt %1

; *** Misc. common
InformationTitle=Thông tin
ConfirmTitle=Xác nhận
ErrorTitle=Lỗi

; *** SetupLdr messages
SetupLdrStartupMessage=Chương trình sẽ cài đặt %1. Bạn có muốn tiếp tục?
LdrCannotCreateTemp=Không thể tạo tập tin tạm thời. Cài đặt bị hủy bỏ
LdrCannotExecTemp=Không thể thực thi tập tin trong thư mục tạm. Cài đặt bị hủy bỏ
HelpTextNote=

; *** Startup error messages
LastErrorMessage=%1.%n%nLỗi %2: %3
SetupFileMissing=Tập tin %1 bị thiếu trong thư mục cài đặt. Vui lòng khắc phục sự cố hoặc lấy bản sao mới của chương trình.
SetupFileCorrupt=Các tập tin cài đặt bị hỏng. Vui lòng lấy bản sao mới của chương trình.
SetupFileCorruptOrWrongVer=Các tập tin cài đặt bị hỏng, hoặc không tương thích với phiên bản của trình cài đặt này. Vui lòng khắc phục sự cố hoặc lấy bản sao mới của chương trình.
InvalidParameter=Tham số không hợp lệ được truyền trên dòng lệnh:%n%n%1
SetupAlreadyRunning=Trình cài đặt đang chạy.
WindowsVersionNotSupported=Chương trình này không hỗ trợ phiên bản Windows mà máy tính của bạn đang chạy.
WindowsServicePackRequired=Chương trình này yêu cầu %1 Service Pack %2 hoặc mới hơn.
NotOnThisPlatform=Chương trình này sẽ không chạy trên %1.
OnlyOnThisPlatform=Chương trình này phải được chạy trên %1.
OnlyOnTheseArchitectures=Chương trình này chỉ có thể được cài đặt trên các phiên bản Windows được thiết kế cho các kiến trúc bộ xử lý sau:%n%n%1
WinVersionTooLowError=Chương trình này yêu cầu %1 phiên bản %2 hoặc mới hơn.
WinVersionTooHighError=Chương trình này không thể được cài đặt trên %1 phiên bản %2 hoặc mới hơn.
AdminPrivilegesRequired=Bạn phải đăng nhập với tư cách quản trị viên khi cài đặt chương trình này.
PowerUserPrivilegesRequired=Bạn phải đăng nhập với tư cách quản trị viên hoặc với tư cách thành viên của nhóm Người dùng Power khi cài đặt chương trình này.
SetupAppRunningError=Trình cài đặt đã phát hiện rằng %1 hiện đang chạy.%n%nVui lòng đóng tất cả các phiên bản của nó ngay bây giờ, sau đó nhấp vào OK để tiếp tục hoặc Hủy để thoát.
UninstallAppRunningError=Trình gỡ cài đặt đã phát hiện rằng %1 hiện đang chạy.%n%nVui lòng đóng tất cả các phiên bản của nó ngay bây giờ, sau đó nhấp vào OK để tiếp tục hoặc Hủy để thoát.

; *** Startup questions
PrivilegesRequiredOverrideTitle=Chọn chế độ cài đặt
PrivilegesRequiredOverrideInstruction=Chọn chế độ cài đặt
PrivilegesRequiredOverrideText1=%1 có thể được cài đặt cho tất cả người dùng (yêu cầu quyền quản trị viên) hoặc chỉ cho bạn.
PrivilegesRequiredOverrideText2=%1 có thể được cài đặt chỉ cho bạn hoặc cho tất cả người dùng (yêu cầu quyền quản trị viên).
PrivilegesRequiredOverrideAllUsers=Cài đặt cho &tất cả người dùng
PrivilegesRequiredOverrideAllUsersRecommended=Cài đặt cho &tất cả người dùng (khuyến nghị)
PrivilegesRequiredOverrideCurrentUser=Cài đặt chỉ cho &tôi
PrivilegesRequiredOverrideCurrentUserRecommended=Cài đặt chỉ cho &tôi (khuyến nghị)

; *** Misc. errors
ErrorCreatingDir=Trình cài đặt không thể tạo thư mục "%1"
ErrorTooManyFilesInDir=Không thể tạo tập tin trong thư mục "%1" vì nó chứa quá nhiều tập tin

; *** Setup common messages
ExitSetupTitle=Thoát khỏi trình cài đặt
ExitSetupMessage=Cài đặt chưa hoàn tất. Nếu bạn thoát ngay bây giờ, chương trình sẽ không được cài đặt.%n%nBạn có thể chạy lại trình cài đặt vào lần khác để hoàn tất cài đặt.%n%nThoát khỏi trình cài đặt?
AboutSetupMenuItem=&Giới thiệu về trình cài đặt...
AboutSetupTitle=Giới thiệu về trình cài đặt
AboutSetupMessage=%1 phiên bản %2%n%3%n%n%1 trang chủ:%n%4
AboutSetupNote=
TranslatorNote=

; *** Buttons
ButtonBack=< &Quay lại
ButtonNext=&Tiếp tục >
ButtonInstall=&Cài đặt
ButtonOK=OK
ButtonCancel=Hủy bỏ
ButtonYes=&Có
ButtonYesToAll=Có với &tất cả
ButtonNo=&Không
ButtonNoToAll=Khô&ng với tất cả
ButtonFinish=&Kết thúc
ButtonBrowse=&Duyệt...
ButtonWizardBrowse=D&uyệt...
ButtonNewFolder=&Tạo thư mục mới

; *** "Select Language" dialog messages
SelectLanguageTitle=Chọn ngôn ngữ cài đặt
SelectLanguageLabel=Chọn ngôn ngữ sử dụng trong quá trình cài đặt.

; *** Common wizard text
ClickNext=Nhấp vào Tiếp tục để tiếp tục hoặc Hủy bỏ để thoát khỏi trình cài đặt.
BeveledLabel=
BrowseDialogTitle=Duyệt tìm thư mục
BrowseDialogLabel=Chọn một thư mục trong danh sách bên dưới, sau đó nhấp vào OK.
NewFolderName=Thư mục mới

; *** "Welcome" wizard page
WelcomeLabel1=Chào mừng đến với trình cài đặt [name]
WelcomeLabel2=Trình cài đặt sẽ cài đặt [name/ver] trên máy tính của bạn.%n%nBạn nên đóng tất cả các ứng dụng khác trước khi tiếp tục.

; *** "Password" wizard page
WizardPassword=Mật khẩu
PasswordLabel1=Cài đặt này được bảo vệ bằng mật khẩu.
PasswordLabel3=Vui lòng cung cấp mật khẩu, sau đó nhấp vào Tiếp tục để tiếp tục. Mật khẩu phân biệt chữ hoa chữ thường.
PasswordEditLabel=&Mật khẩu:
IncorrectPassword=Mật khẩu bạn nhập không chính xác. Vui lòng thử lại.

; *** "License Agreement" wizard page
WizardLicense=Thỏa thuận cấp phép
LicenseLabel=Vui lòng đọc thông tin quan trọng sau trước khi tiếp tục.
LicenseLabel3=Vui lòng đọc thỏa thuận cấp phép sau. Bạn phải chấp nhận các điều khoản của thỏa thuận này trước khi tiếp tục cài đặt.
LicenseAccepted=Tôi &đồng ý với thỏa thuận
LicenseNotAccepted=Tôi &không đồng ý với thỏa thuận

; *** "Information" wizard pages
WizardInfoBefore=Thông tin
InfoBeforeLabel=Vui lòng đọc thông tin quan trọng sau trước khi tiếp tục.
InfoBeforeClickLabel=Khi bạn đã sẵn sàng tiếp tục cài đặt, hãy nhấp vào Tiếp tục.
WizardInfoAfter=Thông tin
InfoAfterLabel=Vui lòng đọc thông tin quan trọng sau trước khi tiếp tục.
InfoAfterClickLabel=Khi bạn đã sẵn sàng tiếp tục cài đặt, hãy nhấp vào Tiếp tục.

; *** "User Information" wizard page
WizardUserInfo=Thông tin người dùng
UserInfoDesc=Vui lòng nhập thông tin của bạn.
UserInfoName=Tên &người dùng:
UserInfoOrg=&Tổ chức:
UserInfoSerial=&Số sê-ri:
UserInfoNameRequired=Bạn phải nhập tên.

; *** "Select Destination Location" wizard page
WizardSelectDir=Chọn vị trí đích
SelectDirDesc=Bạn muốn cài đặt [name] ở đâu?
SelectDirLabel3=Trình cài đặt sẽ cài đặt [name] vào thư mục sau.
SelectDirBrowseLabel=Để tiếp tục, hãy nhấp vào Tiếp tục. Nếu bạn muốn chọn một thư mục khác, hãy nhấp vào Duyệt.
DiskSpaceGBLabel=Cần có ít nhất [gb] GB dung lượng đĩa trống.
DiskSpaceMBLabel=Cần có ít nhất [mb] MB dung lượng đĩa trống.
CannotInstallToNetworkDrive=Trình cài đặt không thể cài đặt vào ổ đĩa mạng.
CannotInstallToUNCPath=Trình cài đặt không thể cài đặt vào đường dẫn UNC.
InvalidPath=Bạn phải nhập đường dẫn đầy đủ với ký tự ổ đĩa; ví dụ:%n%nC:\APP%n%nhoặc đường dẫn UNC ở dạng:%n%n\\server\share
InvalidDrive=Ổ đĩa hoặc chia sẻ UNC bạn đã chọn không tồn tại hoặc không thể truy cập. Vui lòng chọn ổ đĩa khác.
DiskSpaceWarningTitle=Không đủ dung lượng đĩa
DiskSpaceWarning=Trình cài đặt yêu cầu ít nhất %1 KB dung lượng trống để cài đặt, nhưng ổ đĩa đã chọn chỉ có %2 KB khả dụng.%n%nBạn có muốn tiếp tục?
DirNameTooLong=Tên thư mục hoặc đường dẫn quá dài.
InvalidDirName=Tên thư mục không hợp lệ.
BadDirName32=Tên thư mục không được chứa bất kỳ ký tự nào sau:%n%n%1
DirExistsTitle=Thư mục đã tồn tại
DirExists=Thư mục:%n%n%1%n%nđã tồn tại. Bạn có muốn cài đặt vào thư mục đó?
DirDoesntExistTitle=Thư mục không tồn tại
DirDoesntExist=Thư mục:%n%n%1%n%nkhông tồn tại. Bạn có muốn tạo thư mục?

; *** "Select Components" wizard page
WizardSelectComponents=Chọn thành phần
SelectComponentsDesc=Những thành phần nào nên được cài đặt?
SelectComponentsLabel2=Chọn các thành phần bạn muốn cài đặt; bỏ chọn các thành phần bạn không muốn cài đặt. Nhấp vào Tiếp tục khi bạn đã sẵn sàng tiếp tục.
FullInstallation=Cài đặt đầy đủ
CompactInstallation=Cài đặt gọn
CustomInstallation=Cài đặt tùy chỉnh
NoUninstallWarningTitle=Thành phần đã tồn tại
NoUninstallWarning=Trình cài đặt đã phát hiện rằng các thành phần sau đã được cài đặt trên máy tính của bạn:%n%n%1%n%nBỏ chọn các thành phần này sẽ không gỡ cài đặt chúng.%n%nBạn có muốn tiếp tục?
ComponentSize1=%1 KB
ComponentSize2=%1 MB
ComponentsDiskSpaceGBLabel=Lựa chọn hiện tại yêu cầu ít nhất [gb] GB dung lượng đĩa.
ComponentsDiskSpaceMBLabel=Lựa chọn hiện tại yêu cầu ít nhất [mb] MB dung lượng đĩa.

; *** "Select Additional Tasks" wizard page
WizardSelectTasks=Chọn tác vụ bổ sung
SelectTasksDesc=Bạn muốn thực hiện những tác vụ bổ sung nào?
SelectTasksLabel2=Chọn các tác vụ bổ sung bạn muốn trình cài đặt thực hiện trong khi cài đặt [name], sau đó nhấp vào Tiếp tục.

; *** "Select Start Menu Folder" wizard page
WizardSelectProgramGroup=Chọn thư mục menu Start
SelectStartMenuFolderDesc=Trình cài đặt nên đặt lối tắt của chương trình ở đâu?
SelectStartMenuFolderLabel3=Trình cài đặt sẽ tạo lối tắt của chương trình trong thư mục menu Start sau.
SelectStartMenuFolderBrowseLabel=Để tiếp tục, hãy nhấp vào Tiếp tục. Nếu bạn muốn chọn một thư mục khác, hãy nhấp vào Duyệt.
MustEnterGroupName=Bạn phải nhập tên thư mục.
GroupNameTooLong=Tên thư mục hoặc đường dẫn quá dài.
InvalidGroupName=Tên thư mục không hợp lệ.
BadGroupName=Tên thư mục không được chứa bất kỳ ký tự nào sau:%n%n%1
NoProgramGroupCheck2=&Không tạo thư mục menu Start

; *** "Ready to Install" wizard page
WizardReady=Sẵn sàng cài đặt
ReadyLabel1=Trình cài đặt hiện đã sẵn sàng để bắt đầu cài đặt [name] trên máy tính của bạn.
ReadyLabel2a=Nhấp vào Cài đặt để tiếp tục cài đặt hoặc nhấp vào Quay lại nếu bạn muốn xem lại hoặc thay đổi bất kỳ cài đặt nào.
ReadyLabel2b=Nhấp vào Cài đặt để tiếp tục cài đặt.
ReadyMemoUserInfo=Thông tin người dùng:
ReadyMemoDir=Vị trí đích:
ReadyMemoType=Loại cài đặt:
ReadyMemoComponents=Thành phần đã chọn:
ReadyMemoGroup=Thư mục menu Start:
ReadyMemoTasks=Tác vụ bổ sung:

; *** TDownloadWizardPage wizard page and DownloadTemporaryFile
DownloadingLabel2=Đang tải xuống các tập tin bổ sung...
ButtonStopDownload=&Dừng tải xuống
StopDownload=Bạn có chắc chắn muốn dừng tải xuống?
ErrorDownloadAborted=Tải xuống bị hủy bỏ
ErrorDownloadFailed=Tải xuống thất bại: %1 %2
ErrorDownloading=Không thể tải xuống %1. %2
ErrorDownloadSizeFailed=Lấy kích thước thất bại: %1 %2
ErrorProgress=Tiến trình không hợp lệ: %1 của %2
ErrorFileSize=Kích thước tập tin không hợp lệ: mong đợi %1, tìm thấy %2

; *** Archive extraction
ExtractingLabel=Đang giải nén các tập tin...
ButtonStopExtraction=&Dừng giải nén
StopExtraction=Bạn có chắc chắn muốn dừng giải nén?
ErrorExtracting=Không thể giải nén %1. %2
ErrorExtractionAborted=Giải nén bị hủy bỏ
ErrorExtractionFailed=Giải nén thất bại: %1
ArchiveIncorrectPassword=Mật khẩu không chính xác
ArchiveIsCorrupted=Tập tin nén bị hỏng
ArchiveUnsupportedFormat=Định dạng nén không được hỗ trợ

; *** Retry/Cancel actions
RetryCancelSelectAction=Chọn hành động
RetryCancelRetry=&Thử lại
RetryCancelCancel=&Hủy bỏ

; *** Source verification
SourceVerificationFailed=Xác minh nguồn thất bại
VerificationKeyNotFound=Không tìm thấy khóa xác minh
VerificationSignatureDoesntExist=Chữ ký không tồn tại
VerificationSignatureInvalid=Chữ ký không hợp lệ
VerificationFileNameIncorrect=Tên tập tin không chính xác
VerificationFileSizeIncorrect=Kích thước tập tin không chính xác
VerificationFileTagIncorrect=Thẻ tập tin không chính xác
VerificationFileHashIncorrect=Mã băm tập tin không chính xác

; *** "Preparing to Install" wizard page
WizardPreparing=Chuẩn bị cài đặt
PreparingDesc=Trình cài đặt đang chuẩn bị cài đặt [name] trên máy tính của bạn.
PreviousInstallNotCompleted=Cài đặt/gỡ bỏ chương trình trước đó chưa hoàn tất. Bạn sẽ cần khởi động lại máy tính để hoàn tất cài đặt đó.%n%nSau khi khởi động lại máy tính, hãy chạy lại trình cài đặt để hoàn tất cài đặt [name].
CannotContinue=Trình cài đặt không thể tiếp tục. Vui lòng nhấp vào Hủy bỏ để thoát.
ApplicationsFound=Các ứng dụng sau đang sử dụng các tập tin cần được cập nhật bởi trình cài đặt. Bạn nên cho phép trình cài đặt tự động đóng các ứng dụng này.
ApplicationsFound2=Các ứng dụng sau đang sử dụng các tập tin cần được cập nhật bởi trình cài đặt. Bạn nên cho phép trình cài đặt tự động đóng các ứng dụng này. Sau khi cài đặt hoàn tất, trình cài đặt sẽ cố gắng khởi động lại các ứng dụng.
CloseApplications=Tự động &đóng các ứng dụng
DontCloseApplications=&Không đóng các ứng dụng
ErrorCloseApplications=Trình cài đặt không thể tự động đóng tất cả các ứng dụng. Bạn nên đóng tất cả các ứng dụng đang sử dụng các tập tin cần được cập nhật bởi trình cài đặt trước khi tiếp tục.
PrepareToInstallNeedsRestart=Trình cài đặt phải khởi động lại máy tính của bạn. Sau khi khởi động lại máy tính, hãy chạy lại trình cài đặt để hoàn tất cài đặt [name].%n%nBạn có muốn khởi động lại ngay bây giờ?

; *** "Installing" wizard page
WizardInstalling=Đang cài đặt
InstallingLabel=Vui lòng đợi trong khi trình cài đặt cài đặt [name] trên máy tính của bạn.

; *** "Setup Completed" wizard page
FinishedHeadingLabel=Hoàn tất cài đặt [name]
FinishedLabelNoIcons=Trình cài đặt đã hoàn tất cài đặt [name] trên máy tính của bạn.
FinishedLabel=Trình cài đặt đã hoàn tất cài đặt [name] trên máy tính của bạn. Ứng dụng có thể được khởi chạy bằng cách chọn các biểu tượng đã cài đặt.
ClickFinish=Nhấp vào Kết thúc để thoát khỏi trình cài đặt.
FinishedRestartLabel=Để hoàn tất cài đặt [name], trình cài đặt phải khởi động lại máy tính của bạn. Bạn có muốn khởi động lại ngay bây giờ?
FinishedRestartMessage=Để hoàn tất cài đặt [name], trình cài đặt phải khởi động lại máy tính của bạn.%n%nBạn có muốn khởi động lại ngay bây giờ?
ShowReadmeCheck=Có, tôi muốn xem tập tin README
YesRadio=&Có, khởi động lại máy tính ngay bây giờ
NoRadio=&Không, tôi sẽ khởi động lại máy tính sau
RunEntryExec=Chạy %1
RunEntryShellExec=Xem %1

; *** "Setup Needs the Next Disk" stuff
ChangeDiskTitle=Trình cài đặt cần đĩa tiếp theo
SelectDiskLabel2=Vui lòng chèn đĩa %1 và nhấp vào OK.%n%nNếu các tập tin trên đĩa này có thể được tìm thấy trong một thư mục khác với thư mục hiển thị bên dưới, hãy nhập đường dẫn chính xác hoặc nhấp vào Duyệt.
PathLabel=Đườ&ng dẫn:
FileNotInDir2=Tập tin "%1" không thể được tìm thấy trong "%2". Vui lòng chèn đĩa chính xác hoặc chọn một thư mục khác.
SelectDirectoryLabel=Vui lòng chỉ định vị trí của đĩa tiếp theo.

; *** Installation phase messages
SetupAborted=Cài đặt chưa hoàn tất.%n%nVui lòng khắc phục sự cố và chạy lại trình cài đặt.
AbortRetryIgnoreSelectAction=Chọn hành động
AbortRetryIgnoreRetry=&Thử lại
AbortRetryIgnoreIgnore=&Bỏ qua lỗi và tiếp tục
AbortRetryIgnoreCancel=Hủy bỏ cài đặt

; *** Installation status messages
StatusClosingApplications=Đang đóng các ứng dụng...
StatusCreateDirs=Đang tạo thư mục...
StatusExtractFiles=Đang giải nén tập tin...
StatusCreateIcons=Đang tạo lối tắt...
StatusCreateIniEntries=Đang tạo mục INI...
StatusCreateRegistryEntries=Đang tạo mục đăng ký...
StatusRegisterFiles=Đang đăng ký tập tin...
StatusSavingUninstall=Đang lưu thông tin gỡ cài đặt...
StatusRunProgram=Đang hoàn tất cài đặt...
StatusRestartingApplications=Đang khởi động lại các ứng dụng...
StatusRollback=Đang khôi phục các thay đổi...
StatusDownloadFiles=Đang tải xuống các tập tin...

; *** Misc. errors
ErrorInternal2=Lỗi nội bộ: %1
ErrorFunctionFailedNoCode=%1 thất bại
ErrorFunctionFailed=%1 thất bại; mã %2
ErrorFunctionFailedWithMessage=%1 thất bại; mã %2.%n%3
ErrorExecutingProgram=Không thể thực thi tập tin:%n%1

; *** Registry errors
ErrorRegOpenKey=Lỗi mở khóa đăng ký:%n%1\%2
ErrorRegCreateKey=Lỗi tạo khóa đăng ký:%n%1\%2
ErrorRegWriteKey=Lỗi ghi khóa đăng ký:%n%1\%2

; *** INI errors
ErrorIniEntry=Lỗi tạo mục INI trong tập tin "%1".

; *** File copying errors
FileAbortRetryIgnoreSkipNotRecommended=&Bỏ qua tập tin này (không khuyến nghị)
FileAbortRetryIgnoreIgnoreNotRecommended=&Bỏ qua lỗi và tiếp tục (không khuyến nghị)
SourceIsCorrupted=Tập tin nguồn bị hỏng
SourceDoesntExist=Tập tin nguồn "%1" không tồn tại
ExistingFileReadOnly2=Không thể thay thế tập tin hiện có vì nó được đánh dấu là chỉ đọc.
ExistingFileReadOnlyRetry=&Xóa thuộc tính chỉ đọc và thử lại
ExistingFileReadOnlyKeepExisting=&Giữ tập tin hiện có
ErrorReadingExistingDest=Đã xảy ra lỗi khi cố gắng đọc tập tin hiện có:
FileExistsSelectAction=Chọn hành động
FileExists2=Tập tin đã tồn tại.
FileExistsOverwriteExisting=&Ghi đè tập tin hiện có
FileExistsKeepExisting=&Giữ tập tin hiện có
FileExistsOverwriteOrKeepAll=&Làm điều này cho các xung đột tiếp theo
ExistingFileNewerSelectAction=Chọn hành động
ExistingFileNewer2=Tập tin hiện có mới hơn tập tin trình cài đặt đang cố gắng cài đặt.
ExistingFileNewerOverwriteExisting=&Ghi đè tập tin hiện có
ExistingFileNewerKeepExisting=&Giữ tập tin hiện có (khuyến nghị)
ExistingFileNewerOverwriteOrKeepAll=&Làm điều này cho các xung đột tiếp theo
ErrorChangingAttr=Đã xảy ra lỗi khi cố gắng thay đổi thuộc tính của tập tin hiện có:
ErrorCreatingTemp=Đã xảy ra lỗi khi cố gắng tạo tập tin trong thư mục đích:
ErrorReadingSource=Đã xảy ra lỗi khi cố gắng đọc tập tin nguồn:
ErrorCopying=Đã xảy ra lỗi khi cố gắng sao chép tập tin:
ErrorReplacingExistingFile=Đã xảy ra lỗi khi cố gắng thay thế tập tin hiện có:
ErrorRestartReplace=RestartReplace thất bại:
ErrorRenamingTemp=Đã xảy ra lỗi khi cố gắng đổi tên tập tin trong thư mục đích:
ErrorRegisterServer=Không thể đăng ký DLL/OCX: %1
ErrorRegSvr32Failed=RegSvr32 thất bại với mã thoát %1
ErrorRegisterTypeLib=Không thể đăng ký thư viện kiểu: %1

; *** Uninstall display name markings
UninstallDisplayNameMark=%1 (%2)
UninstallDisplayNameMarks=%1 (%2, %3)
UninstallDisplayNameMark32Bit=32-bit
UninstallDisplayNameMark64Bit=64-bit
UninstallDisplayNameMarkAllUsers=Tất cả người dùng
UninstallDisplayNameMarkCurrentUser=Người dùng hiện tại

; *** Post-installation errors
ErrorOpeningReadme=Đã xảy ra lỗi khi cố gắng mở tập tin README.
ErrorRestartingComputer=Trình cài đặt không thể khởi động lại máy tính. Vui lòng thực hiện thao tác này thủ công.

; *** Uninstaller messages
UninstallNotFound=Tập tin "%1" không tồn tại. Không thể gỡ cài đặt.
UninstallOpenError=Tập tin "%1" không thể mở. Không thể gỡ cài đặt
UninstallUnsupportedVer=Tập tin nhật ký gỡ cài đặt "%1" ở định dạng không được nhận dạng bởi phiên bản trình gỡ cài đặt này. Không thể gỡ cài đặt
UninstallUnknownEntry=Đã gặp mục không xác định (%1) trong nhật ký gỡ cài đặt
ConfirmUninstall=Bạn có chắc chắn muốn gỡ bỏ hoàn toàn %1 và tất cả các thành phần của nó?
UninstallOnlyOnWin64=Cài đặt này chỉ có thể được gỡ bỏ trên Windows 64-bit.
OnlyAdminCanUninstall=Cài đặt này chỉ có thể được gỡ bỏ bởi người dùng có quyền quản trị viên.
UninstallStatusLabel=Vui lòng đợi trong khi %1 đang được gỡ bỏ khỏi máy tính của bạn.
UninstalledAll=%1 đã được gỡ bỏ thành công khỏi máy tính của bạn.
UninstalledMost=Gỡ cài đặt %1 hoàn tất.%n%nMột số phần tử không thể được gỡ bỏ. Chúng có thể được gỡ bỏ thủ công.
UninstalledAndNeedsRestart=Để hoàn tất gỡ cài đặt %1, máy tính của bạn phải được khởi động lại.%n%nBạn có muốn khởi động lại ngay bây giờ?
UninstallDataCorrupted=Tập tin "%1" bị hỏng. Không thể gỡ cài đặt

; *** Uninstallation phase messages
ConfirmDeleteSharedFileTitle=Gỡ bỏ tập tin dùng chung?
ConfirmDeleteSharedFile2=Hệ thống cho biết tập tin dùng chung sau đây không còn được sử dụng bởi bất kỳ chương trình nào. Bạn có muốn gỡ cài đặt gỡ bỏ tập tin dùng chung này?%n%nNếu có chương trình nào vẫn đang sử dụng tập tin này và nó bị gỡ bỏ, các chương trình đó có thể không hoạt động đúng. Nếu bạn không chắc chắn, hãy chọn Không. Để lại tập tin trên hệ thống của bạn sẽ không gây hại.
SharedFileNameLabel=Tên tập tin:
SharedFileLocationLabel=Vị trí:
WizardUninstalling=Trạng thái gỡ cài đặt
StatusUninstalling=Đang gỡ cài đặt %1...

; *** Shutdown block reasons
ShutdownBlockReasonInstallingApp=Đang cài đặt %1.
ShutdownBlockReasonUninstallingApp=Đang gỡ cài đặt %1.

; The custom messages below aren't used by Setup itself, but if you make
; use of them in your scripts, you'll want to translate them.

[CustomMessages]

NameAndVersion=%1 phiên bản %2
AdditionalIcons=Biểu tượng bổ sung:
CreateDesktopIcon=Tạo biểu tượng trên &Desktop
CreateQuickLaunchIcon=Tạo biểu tượng &Quick Launch
ProgramOnTheWeb=%1 trên Web
UninstallProgram=Gỡ cài đặt %1
LaunchProgram=Khởi chạy %1
AssocFileExtension=&Liên kết %1 với phần mở rộng tập tin %2
AssocingFileExtension=Đang liên kết %1 với phần mở rộng tập tin %2...
AutoStartProgramGroupDescription=Khởi động:
AutoStartProgram=Tự động khởi chạy %1
AddonHostProgramNotFound=%1 không thể được tìm thấy trong thư mục bạn đã chọn.%n%nBạn có muốn tiếp tục?