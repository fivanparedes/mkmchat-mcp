<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('query_histories', function (Blueprint $table) {
            // 'team_suggest' | 'ask_question'
            $table->string('query_type')->default('team_suggest')->after('strategy');
        });
    }

    public function down(): void
    {
        Schema::table('query_histories', function (Blueprint $table) {
            $table->dropColumn('query_type');
        });
    }
};
