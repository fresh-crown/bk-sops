/**
* Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
* Edition) available.
* Copyright (C) 2017-2020 THL A29 Limited, a Tencent company. All rights reserved.
* Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
* http://opensource.org/licenses/MIT
* Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
* an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
* specific language governing permissions and limitations under the License.
*/
<template>
    <div id="app">
        <navigator v-if="!hideHeader" :appmaker-data-loading="appmakerDataLoading" />
        <div class="main-container">
            <router-view v-if="isRouterViewShow"></router-view>
        </div>
        <ErrorCodeModal ref="errorModal"></ErrorCodeModal>
        <PermissionModal ref="permissionModal"></PermissionModal>
        <permissionApply
            v-if="permissinApplyShow"
            ref="permissionApply"
            :permission-data="permissionData">
        </permissionApply>
    </div>
</template>
<script>
    import { mapState, mapMutations, mapActions } from 'vuex'
    import bus from '@/utils/bus.js'
    import { errorHandler } from '@/utils/errorHandler.js'
    import isCrossOriginIFrame from '@/utils/isCrossOriginIFrame.js'
    import { setConfigContext } from '@/config/setting.js'
    import permission from '@/mixins/permission.js'
    import ErrorCodeModal from '@/components/common/modal/ErrorCodeModal.vue'
    import PermissionModal from '@/components/common/modal/PermissionModal.vue'
    import Navigator from '@/components/layout/Navigator.vue'
    import permissionApply from '@/components/layout/permissionApply.vue'

    export default {
        name: 'App',
        components: {
            Navigator,
            ErrorCodeModal,
            permissionApply,
            PermissionModal
        },
        mixins: [permission],
        provide () {
            return {
                reload: this.reload
            }
        },
        data () {
            return {
                footerLoading: false,
                permissinApplyShow: false,
                permissionData: {
                    type: 'project', // 无权限类型: project、other
                    permission: null
                },
                isRouterAlive: false,
                projectDetailLoading: false, // 项目详情加载
                appmakerDataLoading: false // 轻应用加载 app 详情,
            }
        },
        computed: {
            ...mapState({
                'hideHeader': state => state.hideHeader,
                'viewMode': state => state.view_mode,
                'appId': state => state.app_id,
                'site_url': state => state.site_url
            }),
            ...mapState('project', {
                'project_id': state => state.project_id
            }),
            isRouterViewShow () {
                return !this.permissinApplyShow && this.isRouterAlive && !this.projectDetailLoading
            }
        },
        watch: {
            '$route' (val, oldVal) {
                const prevRouterProjectId = oldVal.params.project_id
                const id = prevRouterProjectId || prevRouterProjectId === 0 ? Number(prevRouterProjectId) : undefined
                this.handleRouteChange(id)
            }
        },
        created () {
            bus.$on('showLoginModal', args => {
                const { has_plain, login_url, width, height, method } = args
                if (has_plain) {
                    const topWindow = isCrossOriginIFrame() ? window : window.top
                    topWindow.BLUEKING.corefunc.open_login_dialog(login_url, width, height, method)
                }
            })
            bus.$on('showErrorModal', (type, responseText, title) => {
                this.$refs.errorModal.show(type, responseText, title)
            })
            bus.$on('togglePermissionApplyPage', (show, type, permission) => {
                this.permissinApplyShow = show
                this.permissionData = {
                    type,
                    permission
                }
                if (!show) {
                    this.isRouterAlive = true
                }
            })
            bus.$on('showPermissionModal', data => {
                this.$refs.permissionModal.show(data)
            })
            bus.$on('showMessage', info => {
                this.$bkMessage({
                    message: info.message,
                    ellipsisLine: info.lines || 1,
                    theme: info.theme || 'error'
                })
            })

            /**
             * 兼容标准插件配置项里，异步请求用到的全局弹窗提示
             */
            window.show_msg = (message, type) => {
                this.$bkMessage({
                    message,
                    ellipsisLine: 2,
                    theme: type
                })
            }
            this.getPageFooter()
        },
        mounted () {
            this.initData()
        },
        methods: {
            ...mapActions([
                'getPermissionMeta',
                'queryUserPermission',
                'getFooterContent'
            ]),
            ...mapActions('appmaker/', [
                'loadAppmakerDetail'
            ]),
            ...mapActions('project', [
                'loadProjectDetail',
                'changeDefaultProject'
            ]),
            ...mapMutations('appmaker/', [
                'setAppmakerTemplateId',
                'setAppmakerDetail'
            ]),
            ...mapMutations('project', [
                'setProjectId',
                'setTimeZone',
                'setProjectName',
                'setProjectActions'
            ]),
            ...mapMutations([
                'setPageFooter',
                'setAdminPerm',
                'setStatisticsPerm'
            ]),
            async initData () {
                if (this.$route.meta.project && this.project_id !== '' && !isNaN(this.project_id)) {
                    await this.getProjectDetail()
                }
                await this.getPermissionMeta()
                if (this.viewMode === 'appmaker') {
                    this.getAppmakerDetail()
                } else {
                    this.queryAdminPerm()
                    this.queryStatisticsPerm()
                }
            },
            async getProjectDetail () {
                try {
                    this.projectDetailLoading = true
                    const projectDetail = await this.loadProjectDetail(this.project_id)
                    this.setProjectId(this.project_id)
                    this.setTimeZone(projectDetail.timeZone)

                    $.atoms = {} // notice: 清除标准插件配置项里的全局变量缓存
                    this.setProjectName(projectDetail.name)
                    this.setProjectActions(projectDetail.auth_actions)
                    if (this.$route.name === 'templateEdit' && this.$route.query.common) {
                        setConfigContext(this.site_url)
                    } else {
                        setConfigContext(this.site_url, projectDetail)
                    }
                    this.changeDefaultProject(this.project_id)
                } catch (err) {
                    errorHandler(err, this)
                } finally {
                    this.projectDetailLoading = false
                }
            },
            async getAppmakerDetail () {
                this.appmakerDataLoading = true
                try {
                    const res = await this.loadAppmakerDetail(this.appId)
                    this.setProjectName(res.project.name)
                    this.setAppmakerDetail(res)
                } catch (e) {
                    errorHandler(e, this)
                } finally {
                    this.appmakerDataLoading = false
                }
            },
            async queryAdminPerm () {
                try {
                    const res = await this.queryUserPermission({
                        action: 'admin_view'
                    })

                    this.setAdminPerm(res.data.is_allow)
                } catch (err) {
                    errorHandler(err, this)
                }
            },
            async queryStatisticsPerm () {
                try {
                    const res = await this.queryUserPermission({
                        action: 'statistics_view'
                    })

                    this.setStatisticsPerm(res.data.is_allow)
                } catch (err) {
                    errorHandler(err, this)
                }
            },
            // 动态获取页面 footer
            async getPageFooter () {
                try {
                    this.footerLoading = true
                    const resp = await this.getFooterContent()
                    if (resp.result) {
                        this.setPageFooter(resp.data)
                    }
                } catch (err) {
                    this.setPageFooter(`<div class="copyright"><div>蓝鲸智云 版权所有</div></div>`)
                    errorHandler(err, this)
                } finally {
                    this.footerLoading = false
                }
            },
            handleRouteChange (preProjectId) {
                this.isRouterAlive = true
                if (!this.$route.meta.project) {
                    this.permissinApplyShow = false
                    setConfigContext(this.site_url)
                } else {
                    // 项目上下文页面
                    if (this.project_id !== '' && !isNaN(this.project_id)) {
                        if (this.project_id !== preProjectId) {
                            this.permissinApplyShow = false
                            this.getProjectDetail()
                        }
                    } else { // 需要项目id页面，id为空时，显示无权限页面
                        this.permissinApplyShow = true
                    }
                }
                if (this.$route.query.template_id !== undefined) {
                    this.setAppmakerTemplateId(this.$route.query.template_id)
                }
            },
            reload () {
                this.isRouterAlive = false
                this.$nextTick(() => {
                    this.isRouterAlive = true
                })
            }
        }
    }
</script>
<style lang="scss">
    @import './scss/app.scss';
    @import '@/scss/config.scss';
    html,body {
        height:100%;
    }
    body.bk-dialog-shown {
        overflow: hidden;
    }
    #app {
        width: 100%;
        height: 100%;
        overflow-x: hidden;
        min-width: 1320px;
    }
    .main-container {
        width: 100%;
        height: calc(100% - 50px);
        min-width: 1320px;
        min-height: calc(100% - 50px);
        overflow-x: hidden;
    }
</style>
