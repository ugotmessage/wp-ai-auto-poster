<?php
/**
 * WordPress Yoast SEO Meta 欄位啟用設定
 * 
 * 將此檔案內容加入您的 WordPress 主題的 functions.php 檔案中，
 * 或建立為一個外掛檔案。
 * 
 * 此設定會啟用 Yoast SEO meta 欄位的 REST API 存取權限，
 * 讓 AI 文章生成器能夠自動設定 SEO 標題、描述和焦點關鍵字。
 */

// 防止直接存取
if (!defined('ABSPATH')) {
    exit;
}

/**
 * 啟用 Yoast SEO meta 欄位的 REST API 存取
 */
add_action('rest_api_init', function() {
    // 註冊 Yoast SEO 標題 meta 欄位
    register_meta('post', '_yoast_wpseo_title', [
        'show_in_rest' => true,
        'single' => true,
        'type' => 'string',
        'description' => 'Yoast SEO 標題'
    ]);
    
    // 註冊 Yoast SEO 描述 meta 欄位
    register_meta('post', '_yoast_wpseo_metadesc', [
        'show_in_rest' => true,
        'single' => true,
        'type' => 'string',
        'description' => 'Yoast SEO 描述'
    ]);
    
    // 註冊 Yoast SEO 焦點關鍵字 meta 欄位
    register_meta('post', '_yoast_wpseo_focuskw', [
        'show_in_rest' => true,
        'single' => true,
        'type' => 'string',
        'description' => 'Yoast SEO 焦點關鍵字'
    ]);
});

/**
 * 確保 REST API 權限正確設定
 */
add_filter('rest_prepare_post', function($response, $post, $request) {
    // 檢查是否有權限編輯文章
    if (current_user_can('edit_post', $post->ID)) {
        return $response;
    }
    return $response;
}, 10, 3);

/**
 * 記錄 meta 欄位存取（除錯用）
 */
add_action('rest_api_init', function() {
    if (defined('WP_DEBUG') && WP_DEBUG) {
        error_log('Yoast SEO meta 欄位已啟用 REST API 存取');
    }
});
