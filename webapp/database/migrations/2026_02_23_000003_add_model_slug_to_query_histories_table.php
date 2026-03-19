<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('query_histories', function (Blueprint $table) {
            $table->string('model_slug')->default('llama3.2:3b');
        });
    }

    public function down(): void
    {
        Schema::table('query_histories', function (Blueprint $table) {
            $table->dropColumn('model_slug');
        });
    }
};
