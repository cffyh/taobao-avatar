## 阿凡达克隆系统是什么 ##

阿凡达是一个基于软件包的应用快照克隆系统，是一个用于集群部署和管理的利器，节约工程师时间的神物。

## 阿凡达克隆系统解决了什么问题 ##

  * 能将已部署的一个应用节点做镜像快照，然后用此快照进行批量部署
  * 解决了整体磁盘镜像需要大容量存储和大量个消耗带宽的问题，阿凡达快照基于文本文件，快照文件大小只有几十到几百K字节，有效减少了集群管理的IO/带宽消耗
  * 解决了集群部署的历史记录问题，使用阿凡达部署集群可以进行整个集群的部署回滚

## 部署场景举例 ##

  * 集群扩容
> > 有没有要在短时间内扩容成百上千甚至万台应用节点的经历？自编脚本加并发工具仍然手忙脚乱，出现失误就是悲剧灾难，尝试用全新的方式扩容你的集群吧，下载观看[演示录像](http://www.box.net/shared/ehzssy404s)
  * 集群回滚
> > 新版上线后出现重大问题要求回滚？天啊，这么大的集群要恢复到上一次状态简直就是抽筋扒皮。看看用阿凡达的方式做这件事有多么的精准和简单吧！
  * 初始化环境
> > 开发人员需要一套标准的开发环境，身为系统管理员你会反复做这样的乏味而简单的工作吗？当然不！直接将阿凡达接入系统克隆交付流程，你会忘记这曾经是一份工作！
  * 应用环境的传递
> > 开发工程师做出了一个复杂的应用，要安装好多软件和修改好多系统配置，身为测试和部署工程师你一定为重构一摸一样的应用而花费大量时间，花费这样的时间真的值得吗？使用阿凡达进行工作结果的传递媒介，你会发现快速构建和瞬间学习变为了现实！

## 系统特色 ##

  * 部署方便——对集群环境要求极低，节点系统 Bash >= 3.0，Perl >= 5.0 即可使用
  * 节约资源——克隆原理基于软件包管理器，克隆整个应用无需存储完整的应用和操作系统实体数据，极大的节省了存储空间；传输数据量为软件包的差异化增量，能有效减少克隆应用时所消耗的带宽
  * 扩容简单——集群管理可扩容性强，可通过增加软件包下载服务器镜像方式轻松扩容
  * 性能强劲——并发能力强，占用运维资源低，通讯简单，单中心服务器可支撑10个以上不同地域每机房主机数量在2000左右的机房
  * 管理简单——兼容Windows/Linux/MAC的SVN GUI工具、多用户管理、权限控制、快照继承、多人协作让管理工作得心应手，如虎添翼