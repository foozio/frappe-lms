<template>
	<div class="container mx-auto px-4 py-6">
		<div class="mb-6">
			<h1 class="text-3xl font-bold text-gray-900 mb-2">Points Dashboard</h1>
			<p class="text-gray-600">Track your learning progress and achievements</p>
		</div>

		<!-- Points Overview Cards -->
		<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
			<!-- Total Points -->
			<div class="bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg p-6 text-white">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold mb-1">Total Points</h3>
						<p class="text-3xl font-bold">{{ userStats?.total_points || 0 }}</p>
					</div>
					<div class="text-4xl opacity-80">
						🏆
					</div>
				</div>
			</div>

			<!-- Available Points -->
			<div class="bg-gradient-to-r from-green-500 to-green-600 rounded-lg p-6 text-white">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold mb-1">Available Points</h3>
						<p class="text-3xl font-bold">{{ userStats?.available_points || 0 }}</p>
					</div>
					<div class="text-4xl opacity-80">
						💎
					</div>
				</div>
			</div>

			<!-- Current Streak -->
			<div class="bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg p-6 text-white">
				<div class="flex items-center justify-between">
					<div>
						<h3 class="text-lg font-semibold mb-1">Current Streak</h3>
						<p class="text-3xl font-bold">{{ userStats?.current_streak || 0 }}</p>
						<p class="text-orange-100 text-sm">days</p>
					</div>
					<div class="text-4xl opacity-80">
						🔥
					</div>
				</div>
			</div>
		</div>

		<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
			<!-- Recent Transactions -->
			<div class="bg-white rounded-lg shadow-sm border">
				<div class="p-6 border-b">
					<h2 class="text-xl font-semibold text-gray-900">Recent Transactions</h2>
				</div>
				
				<div v-if="transactionsResource.loading" class="p-6">
					<div class="animate-pulse space-y-4">
						<div v-for="i in 5" :key="i" class="flex items-center space-x-4">
							<div class="w-10 h-10 bg-gray-200 rounded-full"></div>
							<div class="flex-1 space-y-2">
								<div class="h-4 bg-gray-200 rounded w-3/4"></div>
								<div class="h-3 bg-gray-200 rounded w-1/2"></div>
							</div>
							<div class="h-4 bg-gray-200 rounded w-16"></div>
						</div>
					</div>
				</div>

				<div v-else-if="recentTransactions.length === 0" class="p-6 text-center text-gray-500">
					<p>No transactions yet. Start learning to earn points!</p>
				</div>

				<div v-else class="divide-y divide-gray-100 max-h-96 overflow-y-auto">
					<div
						v-for="transaction in recentTransactions"
						:key="transaction.name"
						class="p-4 hover:bg-gray-50 transition-colors"
					>
						<div class="flex items-center justify-between">
							<div class="flex items-center space-x-3">
								<!-- Transaction Type Icon -->
								<div
									:class="[
										'w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold',
										transaction.transaction_type === 'earned' ? 'bg-green-100 text-green-800' :
										transaction.transaction_type === 'redeemed' ? 'bg-red-100 text-red-800' :
										'bg-blue-100 text-blue-800'
									]"
								>
									{{ getTransactionIcon(transaction.transaction_type) }}
								</div>

								<div>
									<div class="font-medium text-gray-900">{{ transaction.activity_type }}</div>
									<div class="text-sm text-gray-500">{{ formatDate(transaction.creation) }}</div>
									<div v-if="transaction.description" class="text-sm text-gray-600 mt-1">
										{{ transaction.description }}
									</div>
								</div>
							</div>

							<div class="text-right">
								<div
									:class="[
										'font-bold text-lg',
										transaction.transaction_type === 'earned' ? 'text-green-600' :
										transaction.transaction_type === 'redeemed' ? 'text-red-600' :
										'text-blue-600'
									]"
								>
									{{ transaction.transaction_type === 'redeemed' ? '-' : '+' }}{{ transaction.points }}
								</div>
								<div class="text-sm text-gray-500">points</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Achievements & Progress -->
			<div class="bg-white rounded-lg shadow-sm border">
				<div class="p-6 border-b">
					<h2 class="text-xl font-semibold text-gray-900">Achievements & Progress</h2>
				</div>

				<div class="p-6 space-y-6">
					<!-- Level Progress -->
					<div>
						<div class="flex items-center justify-between mb-2">
							<span class="text-sm font-medium text-gray-700">Level {{ currentLevel }}</span>
							<span class="text-sm text-gray-500">{{ userStats?.total_points || 0 }} / {{ nextLevelPoints }} points</span>
						</div>
						<div class="w-full bg-gray-200 rounded-full h-2">
							<div
								class="bg-blue-600 h-2 rounded-full transition-all duration-300"
								:style="{ width: levelProgress + '%' }"
							></div>
						</div>
					</div>

					<!-- Recent Achievements -->
					<div>
						<h3 class="text-lg font-medium text-gray-900 mb-4">Recent Achievements</h3>
						<div v-if="recentAchievements.length === 0" class="text-center text-gray-500 py-4">
							<p>No achievements yet. Keep learning!</p>
						</div>
						<div v-else class="space-y-3">
							<div
								v-for="achievement in recentAchievements"
								:key="achievement.name"
								class="flex items-center space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200"
							>
								<div class="text-2xl">🏅</div>
								<div class="flex-1">
									<div class="font-medium text-gray-900">{{ achievement.activity_type }}</div>
									<div class="text-sm text-gray-600">{{ formatDate(achievement.creation) }}</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Quick Stats -->
					<div class="grid grid-cols-2 gap-4">
						<div class="text-center p-4 bg-gray-50 rounded-lg">
							<div class="text-2xl font-bold text-gray-900">{{ userStats?.longest_streak || 0 }}</div>
							<div class="text-sm text-gray-600">Longest Streak</div>
						</div>
						<div class="text-center p-4 bg-gray-50 rounded-lg">
							<div class="text-2xl font-bold text-gray-900">{{ totalTransactions }}</div>
							<div class="text-sm text-gray-600">Total Activities</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { createResource } from 'frappe-ui'
import { sessionStore } from '@/stores/session'

const { $session } = sessionStore()

// User stats resource
const userStatsResource = createResource({
	url: 'lms.api.get_user_points_stats',
	auto: true
})

// Recent transactions resource
const transactionsResource = createResource({
	url: 'lms.api.get_user_points_transactions',
	params: {
		limit: 10
	},
	auto: true
})

const userStats = computed(() => {
	return userStatsResource.data
})

const recentTransactions = computed(() => {
	return transactionsResource.data || []
})

const recentAchievements = computed(() => {
	return recentTransactions.value.filter(t => 
		t.activity_type && ['course_completed', 'quiz_passed', 'assignment_submitted'].includes(t.activity_type)
	).slice(0, 3)
})

const totalTransactions = computed(() => {
	return recentTransactions.value.length
})

// Level calculation
const currentLevel = computed(() => {
	const points = userStats.value?.total_points || 0
	return Math.floor(points / 1000) + 1
})

const nextLevelPoints = computed(() => {
	return currentLevel.value * 1000
})

const levelProgress = computed(() => {
	const points = userStats.value?.total_points || 0
	const currentLevelStart = (currentLevel.value - 1) * 1000
	const progressInLevel = points - currentLevelStart
	return Math.min((progressInLevel / 1000) * 100, 100)
})

const getTransactionIcon = (type) => {
	switch (type) {
		case 'earned': return '+'
		case 'redeemed': return '-'
		case 'bonus': return '★'
		default: return '•'
	}
}

const formatDate = (dateString) => {
	const date = new Date(dateString)
	return date.toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric'
	})
}

onMounted(() => {
	userStatsResource.reload()
	transactionsResource.reload()
})
</script>