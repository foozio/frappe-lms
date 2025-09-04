<template>
	<div
		:class="[
			'flex items-center p-4 rounded-lg transition-colors',
			isCurrentUser ? 'bg-blue-50 border-2 border-blue-200' : 'bg-white hover:bg-gray-50',
			!isCurrentUser && 'border border-gray-200'
		]"
	>
		<!-- Rank -->
		<div class="flex-shrink-0 w-12 text-center">
			<div
				v-if="entry.rank <= 3"
				:class="[
					'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm mx-auto',
					entry.rank === 1 ? 'bg-yellow-500' :
					entry.rank === 2 ? 'bg-gray-400' :
					'bg-amber-600'
				]"
			>
				{{ getRankDisplay() }}
			</div>
			<div v-else class="text-lg font-semibold text-gray-600">
				#{{ entry.rank }}
			</div>
		</div>

		<!-- User Avatar -->
		<div class="flex-shrink-0 ml-4">
			<div class="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
				<img
					v-if="entry.user_image"
					:src="entry.user_image"
					:alt="entry.full_name"
					class="w-10 h-10 rounded-full object-cover"
				/>
				<span v-else class="text-gray-600 font-medium text-sm">
					{{ getInitials(entry.full_name) }}
				</span>
			</div>
		</div>

		<!-- User Info -->
		<div class="flex-1 ml-4">
			<div class="flex items-center">
				<h3
					:class="[
						'font-semibold',
						isCurrentUser ? 'text-blue-900' : 'text-gray-900'
					]"
				>
					{{ entry.full_name }}
					<span v-if="isCurrentUser" class="ml-2 text-blue-600 text-sm">(You)</span>
				</h3>
			</div>
			<div class="flex items-center mt-1 text-sm text-gray-600">
				<span v-if="entry.title" class="mr-3">{{ entry.title }}</span>
				<span v-if="showLevel" class="mr-3">Level {{ getUserLevel() }}</span>
			</div>
		</div>

		<!-- Points -->
		<div class="flex-shrink-0">
			<PointsBadge
				:points="entry.total_points"
				:variant="isCurrentUser ? 'primary' : 'gray'"
				size="md"
			/>
		</div>

		<!-- Streak (if available) -->
		<div v-if="entry.current_streak !== undefined" class="flex-shrink-0 ml-3">
			<StreakBadge :streak="entry.current_streak" size="sm" />
		</div>

		<!-- Trend Indicator -->
		<div v-if="showTrend && entry.trend" class="flex-shrink-0 ml-3">
			<div
				:class="[
					'flex items-center text-xs px-2 py-1 rounded-full',
					entry.trend === 'up' ? 'bg-green-100 text-green-700' :
					entry.trend === 'down' ? 'bg-red-100 text-red-700' :
					'bg-gray-100 text-gray-600'
				]"
			>
				<span class="mr-1">
					{{ entry.trend === 'up' ? '↗️' : entry.trend === 'down' ? '↘️' : '➡️' }}
				</span>
				<span>{{ entry.trend_value || 0 }}</span>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from 'vue'
import PointsBadge from './PointsBadge.vue'
import StreakBadge from './StreakBadge.vue'

const props = defineProps({
	entry: {
		type: Object,
		required: true
	},
	isCurrentUser: {
		type: Boolean,
		default: false
	},
	showLevel: {
		type: Boolean,
		default: true
	},
	showTrend: {
		type: Boolean,
		default: false
	}
})

const getRankDisplay = () => {
	if (props.entry.rank === 1) return '🥇'
	if (props.entry.rank === 2) return '🥈'
	if (props.entry.rank === 3) return '🥉'
	return props.entry.rank
}

const getInitials = (name) => {
	if (!name) return '?'
	return name
		.split(' ')
		.map(word => word.charAt(0))
		.join('')
		.toUpperCase()
		.slice(0, 2)
}

const getUserLevel = () => {
	// Calculate level based on points (same logic as in PointsDashboard)
	const points = props.entry.total_points || 0
	return Math.floor(points / 1000) + 1
}
</script>